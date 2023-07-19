import { config } from '@grafana/runtime';
import dayjs from 'dayjs';
import { action, computed, observable } from 'mobx';

import { UserAvailability } from 'containers/EscalationVariants/EscalationVariants.types';
import BaseStore from 'models/base_store';
import { NotificationChoices, NotificationPolicyType, NotifyByOption } from 'models/notification_policy';
import { makeRequest } from 'network';
import { Mixpanel } from 'services/mixpanel';
import { RootStore } from 'state';
import { move } from 'state/helpers';
import { throttlingError } from 'utils';
import { isUserActionAllowed, UserActions } from 'utils/authorization';
import { PageNumberPaginatedApiResponse } from 'utils/pagination/types';

import { getTimezone, prepareForUpdate } from './user.helpers';
import { User } from './user.types';

type UserId = User['pk'];
type NotificationPolicyId = NotificationPolicyType['id'];

type UserNotificationPolicies = NotificationPolicyType[];
type NotifyByOptions = NotifyByOption[];

type UserPayload = Partial<User>;

type UserIdToUserMap = Record<UserId, User>;
type UserIdToUserNotificationPolicyMap = Record<UserId, UserNotificationPolicies>;

type PaginatedAPIResponse = PageNumberPaginatedApiResponse<User>;

type NotificationPolicyOptionsAPIResponse = {
  actions: {
    POST: NotificationChoices;
  };
};

type GetTelegramVerificationCodeAPIResponse = {
  telegram_code: string;
  bot_link: string;
};

type _BaseICalLinkAPIResponse = {
  created_at: string;
};

type GetIcalLinkAPIResponse = _BaseICalLinkAPIResponse & {
  revoked_at: string | null;
  active: boolean;
};

type CreateIcalLinkAPIResponse = _BaseICalLinkAPIResponse & {
  token: string;
  export_url: string;
};

export class UserStore extends BaseStore {
  @observable.shallow
  searchResult: PageNumberPaginatedApiResponse<UserId> = null;

  @observable.shallow
  items: UserIdToUserMap = {};

  itemsCurrentlyUpdating: Record<UserId, boolean> = {};

  @observable
  notificationPolicies: UserIdToUserNotificationPolicyMap = {};

  @observable
  notificationChoices: NotificationChoices = null;

  @observable
  notifyByOptions: NotifyByOptions = [];

  @observable
  isTestCallInProgress = false;

  @observable
  currentUserPk?: UserId;

  currentUserPath = '/user/';
  notificationPoliciesPath = '/notification_policies/';

  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/users/';
  }

  @computed
  get currentUser(): User {
    if (!this.currentUserPk) {
      return undefined;
    }
    return this.items[this.currentUserPk];
  }

  @action
  async loadCurrentUser(updateTimezone = true): Promise<void> {
    const response = await makeRequest<User>(this.currentUserPath);
    const { pk: currentUserPk } = response;

    let timezone = response.timezone;

    if (updateTimezone) {
      timezone = await this.refreshTimezone(currentUserPk);
    }

    this.items = {
      ...this.items,
      [currentUserPk]: { ...response, timezone },
    };

    this.currentUserPk = currentUserPk;
  }

  @action
  async refreshTimezone(id: UserId): Promise<string> {
    const { timezone: grafanaPreferencesTimezone } = config.bootData.user;
    const timezone = grafanaPreferencesTimezone === 'browser' ? dayjs.tz.guess() : grafanaPreferencesTimezone;
    if (isUserActionAllowed(UserActions.UserSettingsWrite)) {
      this.update(id, { timezone });
    }

    this.rootStore.currentTimezone = timezone;

    return timezone;
  }

  async _fetchUserWithDefaultTimezone(userPk: UserId, skipErrorHandling = false): Promise<User | void> {
    const user = await this.getById<User>(userPk, skipErrorHandling);

    if (!user) {
      return;
    }

    return {
      ...user,
      timezone: getTimezone(user),
    };
  }

  @action
  async loadUser(userPk: UserId, skipErrorHandling = false): Promise<User | void> {
    const user = await this._fetchUserWithDefaultTimezone(userPk, skipErrorHandling);

    if (!user) {
      return;
    }

    this.items = { ...this.items, [userPk]: user };
    return user;
  }

  @action
  async updateItem(userPk: UserId): Promise<void> {
    if (this.itemsCurrentlyUpdating[userPk]) {
      return;
    }

    this.itemsCurrentlyUpdating[userPk] = true;

    const user = await this._fetchUserWithDefaultTimezone(userPk);
    if (!user) {
      return;
    }

    this.items = { ...this.items, [userPk]: user };

    delete this.itemsCurrentlyUpdating[userPk];
  }

  @action
  async updateItems(search = '', page = 1): Promise<void> {
    const { results, ...pagination } = await makeRequest<PaginatedAPIResponse>(this.path, {
      params: { search, page },
    });

    this.items = {
      ...this.items,
      ...results.reduce(
        (acc, item) => ({
          ...acc,
          [item.pk]: {
            ...item,
            timezone: getTimezone(item),
          },
        }),
        {} as UserIdToUserMap
      ),
    };

    this.searchResult = {
      ...pagination,
      results: results.map(({ pk }) => pk),
    };
  }

  getSearchResult(): PaginatedAPIResponse | void {
    const { searchResult } = this;

    if (!searchResult) {
      return;
    }

    return {
      ...searchResult,
      results: searchResult.results.map((userPk) => this.items[userPk]),
    };
  }

  sendTelegramConfirmationCode = (userPk: UserId): Promise<GetTelegramVerificationCodeAPIResponse> =>
    makeRequest<GetTelegramVerificationCodeAPIResponse>(`${this.path}${userPk}/get_telegram_verification_code/`);

  @action
  unlinkSlack = async (userPk: UserId): Promise<void> => {
    await makeRequest<null>(`${this.path}${userPk}/unlink_slack/`, {
      method: 'POST',
    });

    const user = await this._fetchUserWithDefaultTimezone(userPk);
    if (!user) {
      return;
    }

    this.items = {
      ...this.items,
      [userPk]: user,
    };
  };

  @action
  unlinkTelegram = async (userPk: UserId): Promise<void> => {
    await makeRequest<null>(`${this.path}${userPk}/unlink_telegram/`, {
      method: 'POST',
    });

    const user = await this._fetchUserWithDefaultTimezone(userPk);
    if (!user) {
      return;
    }

    this.items = {
      ...this.items,
      [userPk]: user,
    };
  };

  sendBackendConfirmationCode = (userPk: UserId, backend: string): Promise<string> =>
    makeRequest<string>(`${this.path}${userPk}/get_backend_verification_code?backend=${backend}`, {
      method: 'GET',
    });

  @action
  unlinkBackend = async (userPk: UserId, backend: string): Promise<void> => {
    await makeRequest<null>(`${this.path}${userPk}/unlink_backend/?backend=${backend}`, {
      method: 'POST',
    });

    this.loadCurrentUser(false);
  };

  @action
  async createUser(data: UserPayload): Promise<User | void> {
    const user = await this.create<User>(data);

    if (!user) {
      return;
    }

    this.items = {
      ...this.items,
      [user.pk]: user,
    };

    return user;
  }

  @action
  async updateUser(data: UserPayload): Promise<void> {
    const { pk: userPk } = data;

    const user = await makeRequest<User>(`${this.path}${userPk}/`, {
      method: 'PUT',
      data: {
        ...prepareForUpdate(this.items[userPk]),
        ...data,
      },
    });

    if (userPk === this.currentUserPk) {
      this.loadCurrentUser(false);
    }

    this.items = {
      ...this.items,
      [userPk]: user,
    };
  }

  @action
  async updateCurrentUser(data: UserPayload): Promise<void> {
    const user = await makeRequest<User>(this.currentUserPath, {
      method: 'PUT',
      data: {
        ...prepareForUpdate(this.items[this.currentUserPk]),
        ...data,
      },
    });

    this.items = {
      ...this.items,
      [this.currentUserPk]: user,
    };
  }

  @action
  async fetchVerificationCode(userPk: UserId, recaptchaToken: string): Promise<void> {
    await makeRequest<null>(`${this.path}${userPk}/get_verification_code/`, {
      method: 'GET',
      headers: { 'X-OnCall-Recaptcha': recaptchaToken },
    }).catch(throttlingError);
  }

  @action
  async fetchVerificationCall(userPk: UserId, recaptchaToken: string): Promise<void> {
    await makeRequest<null>(`${this.path}${userPk}/get_verification_call/`, {
      method: 'GET',
      headers: { 'X-OnCall-Recaptcha': recaptchaToken },
    }).catch(throttlingError);
  }

  @action
  async verifyPhone(userPk: UserId, token: string): Promise<void> {
    return await makeRequest<null>(`${this.path}${userPk}/verify_number/?token=${token}`, {
      method: 'PUT',
    }).catch(throttlingError);
  }

  @action
  forgetPhone = (userPk: UserId): Promise<void> =>
    makeRequest<null>(`${this.path}${userPk}/forget_number/`, {
      method: 'PUT',
    });

  @action
  async updateNotificationPolicies(id: UserId): Promise<void> {
    const _fetchNotificationPolicies = (important: boolean) =>
      makeRequest<UserNotificationPolicies>(this.notificationPoliciesPath, {
        params: { user: id, important },
      });

    const importantEPs = await _fetchNotificationPolicies(true);
    const nonImportantEPs = await _fetchNotificationPolicies(false);

    this.notificationPolicies = {
      ...this.notificationPolicies,
      [id]: [...nonImportantEPs, ...importantEPs],
    };
  }

  @action
  async moveNotificationPolicyToPosition(
    userPk: UserId,
    oldIndex: number,
    newIndex: number,
    offset: number
  ): Promise<void> {
    Mixpanel.track('Move NotificationPolicy', null);
    const notificationPolicy = this.notificationPolicies[userPk][oldIndex + offset];

    this.notificationPolicies[userPk] = move(this.notificationPolicies[userPk], oldIndex + offset, newIndex + offset);

    await makeRequest<null>(
      `${this.notificationPoliciesPath}${notificationPolicy.id}/move_to_position/?position=${newIndex}`,
      {
        method: 'PUT',
      }
    );

    this.updateNotificationPolicies(userPk);

    this.updateItem(userPk); // to update notification_chain_verbal
  }

  @action
  async addNotificationPolicy(userPk: UserId, important: NotificationPolicyType['important']): Promise<void> {
    await makeRequest<NotificationPolicyType>(this.notificationPoliciesPath, {
      method: 'POST',
      data: { user: userPk, important },
    });

    this.updateNotificationPolicies(userPk);

    this.updateItem(userPk); // to update notification_chain_verbal
  }

  @action
  async updateNotificationPolicy(userPk: UserId, id: NotificationPolicyId, value: NotificationPolicyType) {
    const notificationPolicy = await makeRequest(`/notification_policies/${id}/`, {
      method: 'PUT',
      data: value,
    });

    this.notificationPolicies = {
      ...this.notificationPolicies,
      [userPk]: this.notificationPolicies[userPk].map((policy) =>
        id === policy.id ? { ...policy, ...notificationPolicy } : policy
      ),
    };

    this.updateItem(userPk); // to update notification_chain_verbal
  }

  @action
  async deleteNotificationPolicy(userPk: UserId, id: NotificationPolicyId): Promise<void> {
    Mixpanel.track('Delete NotificationPolicy', null);

    await makeRequest(`${this.notificationPoliciesPath}${id}`, { method: 'DELETE' });

    this.updateNotificationPolicies(userPk);

    this.updateItem(userPk); // to update notification_chain_verbal
  }

  @action
  async updateNotificationPolicyOptions(): Promise<void> {
    const response = await makeRequest<NotificationPolicyOptionsAPIResponse>(this.notificationPoliciesPath, {
      method: 'OPTIONS',
    });

    this.notificationChoices = response.actions.POST;
  }

  @action
  sendTestPushNotification = (userId: UserId, isCritical: boolean): Promise<void> =>
    makeRequest<null>(`${this.path}${userId}/send_test_push`, {
      method: 'POST',
      params: {
        critical: isCritical,
      },
    });

  @action
  async updateNotifyByOptions() {
    this.notifyByOptions = await makeRequest<NotifyByOptions>(`${this.notificationPoliciesPath}notify_by_options/`);
  }

  async makeTestCall(userPk: UserId): Promise<void> {
    this.isTestCallInProgress = true;

    await makeRequest<null>(`${this.path}${userPk}/make_test_call/`, {
      method: 'POST',
    })
      .catch(this.onApiError)
      .finally(() => {
        this.isTestCallInProgress = false;
      });
  }

  async sendTestSms(userPk: UserId): Promise<void> {
    this.isTestCallInProgress = true;

    await makeRequest<null>(`${this.path}${userPk}/send_test_sms/`, {
      method: 'POST',
    })
      .catch(this.onApiError)
      .finally(() => {
        this.isTestCallInProgress = false;
      });
  }

  getiCalLink = (userPk: UserId): Promise<GetIcalLinkAPIResponse> =>
    makeRequest<GetIcalLinkAPIResponse>(`${this.path}${userPk}/export_token/`, {
      method: 'GET',
    });

  createiCalLink = (userPk: UserId): Promise<CreateIcalLinkAPIResponse> =>
    makeRequest<CreateIcalLinkAPIResponse>(`${this.path}${userPk}/export_token/`, {
      method: 'POST',
    });

  deleteiCalLink = (userPk: UserId): Promise<void> =>
    makeRequest<null>(`${this.path}${userPk}/export_token/`, {
      method: 'DELETE',
    });

  checkUserAvailability = (userPk: UserId): Promise<UserAvailability> =>
    makeRequest<UserAvailability>(`${this.path}${userPk}/check_availability/`, {
      method: 'GET',
    });
}
