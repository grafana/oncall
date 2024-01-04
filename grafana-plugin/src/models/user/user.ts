import { config } from '@grafana/runtime';
import dayjs from 'dayjs';
import { get } from 'lodash-es';
import { action, computed, observable, makeObservable, runInAction } from 'mobx';

import BaseStore from 'models/base_store';
import { NotificationPolicyType } from 'models/notification_policy/notification_policy';
import { makeRequest } from 'network';
import { RootStore } from 'state';
import { move } from 'state/helpers';
import { throttlingError } from 'utils';
import { isUserActionAllowed, UserActions } from 'utils/authorization';

import { getTimezone, prepareForUpdate } from './user.helpers';
import { User } from './user.types';

export type PaginatedUsersResponse<UT = User> = {
  count: number;
  page_size: number;
  results: UT[];
};

export class UserStore extends BaseStore {
  @observable.shallow
  searchResult: { count?: number; results?: Array<User['pk']>; page_size?: number } = {};

  @observable.shallow
  items: { [pk: string]: User } = {};

  itemsCurrentlyUpdating = {};

  @observable
  notificationPolicies: any = {};

  @observable
  notificationChoices: any = [];

  @observable
  notifyByOptions: any = [];

  @observable
  isTestCallInProgress = false;

  @observable
  currentUserPk?: User['pk'];

  constructor(rootStore: RootStore) {
    super(rootStore);

    makeObservable(this);

    this.path = '/users/';
  }

  @computed
  get currentUser() {
    if (!this.currentUserPk) {
      return undefined;
    }
    return this.items[this.currentUserPk as User['pk']];
  }

  @action
  async loadCurrentUser() {
    const response = await makeRequest('/user/', {});
    const timezone = await this.refreshTimezone(response.pk);

    runInAction(() => {
      this.items = {
        ...this.items,
        [response.pk]: { ...response, timezone },
      };
      this.currentUserPk = response.pk;
    });
  }

  @action
  async refreshTimezone(id: User['pk']) {
    const { timezone: grafanaPreferencesTimezone } = config.bootData.user;
    const timezone = grafanaPreferencesTimezone === 'browser' ? dayjs.tz.guess() : grafanaPreferencesTimezone;
    if (isUserActionAllowed(UserActions.UserSettingsWrite)) {
      this.update(id, { timezone });
    }

    this.rootStore.timezoneStore.setSelectedTimezoneOffsetBasedOnTz(timezone);

    return timezone;
  }

  @action
  async loadUser(userPk: User['pk'], skipErrorHandling = false): Promise<User> {
    const user = await this.getById(userPk, skipErrorHandling);

    runInAction(() => {
      this.items = {
        ...this.items,
        [user.pk]: { ...user, timezone: getTimezone(user) },
      };
    });

    return user;
  }

  @action
  async updateItem(userPk: User['pk']) {
    if (this.itemsCurrentlyUpdating[userPk]) {
      return;
    }

    this.itemsCurrentlyUpdating[userPk] = true;

    const user = await this.getById(userPk);

    runInAction(() => {
      this.items = {
        ...this.items,
        [user.pk]: { ...user, timezone: getTimezone(user) },
      };
    });

    delete this.itemsCurrentlyUpdating[userPk];
  }

  /**
   * NOTE: if is_currently_oncall=all the backend will not paginate the results, it will send back an array of ALL users
   */
  async search<RT = PaginatedUsersResponse<User>>(f: any = { searchTerm: '' }, page = 1): Promise<RT> {
    const filters = typeof f === 'string' ? { searchTerm: f } : f; // for GSelect compatibility
    const { searchTerm: search, ...restFilters } = filters;
    return makeRequest<RT>(this.path, {
      params: { search, page, ...restFilters },
    });
  }

  @action
  async updateItems(f: any = { searchTerm: '' }, page = 1, invalidateFn?: () => boolean): Promise<any> {
    const response = await this.search(f, page);

    if (invalidateFn && invalidateFn()) {
      return;
    }

    const { count, results, page_size } = response;

    runInAction(() => {
      this.items = {
        ...this.items,
        ...results.reduce(
          (acc: { [key: number]: User }, item: User) => ({
            ...acc,
            [item.pk]: {
              ...item,
              timezone: getTimezone(item),
            },
          }),
          {}
        ),
      };

      this.searchResult = {
        count,
        page_size,
        results: results.map((item: User) => item.pk),
      };
    });

    return response;
  }

  getSearchResult() {
    return {
      page_size: this.searchResult.page_size,
      count: this.searchResult.count,
      results: this.searchResult.results?.map((userPk: User['pk']) => this.items?.[userPk]),
    };
  }

  sendTelegramConfirmationCode = async (userPk: User['pk']) => {
    return await makeRequest(`/users/${userPk}/get_telegram_verification_code/`, {});
  };

  @action
  unlinkSlack = async (userPk: User['pk']) => {
    await makeRequest(`/users/${userPk}/unlink_slack/`, {
      method: 'POST',
    });

    const user = await this.getById(userPk);

    runInAction(() => {
      this.items = {
        ...this.items,
        [user.pk]: user,
      };
    });
  };

  @action
  unlinkTelegram = async (userPk: User['pk']) => {
    await makeRequest(`/users/${userPk}/unlink_telegram/`, {
      method: 'POST',
    });

    const user = await this.getById(userPk);

    runInAction(() => {
      this.items = {
        ...this.items,
        [user.pk]: user,
      };
    });
  };

  sendBackendConfirmationCode = (userPk: User['pk'], backend: string) =>
    makeRequest<string>(`/users/${userPk}/get_backend_verification_code?backend=${backend}`, {
      method: 'GET',
    });

  @action
  unlinkBackend = async (userPk: User['pk'], backend: string) => {
    await makeRequest(`/users/${userPk}/unlink_backend/?backend=${backend}`, {
      method: 'POST',
    });

    this.loadCurrentUser();
  };

  @action
  async createUser(data: any) {
    const user = await this.create(data);

    runInAction(() => {
      this.items = {
        ...this.items,
        [user.pk]: user,
      };
    });

    return user;
  }

  @action
  async updateUser(data: Partial<User>) {
    const user = await makeRequest(`/users/${data.pk}/`, {
      method: 'PUT',
      data: {
        ...prepareForUpdate(this.items[data.pk as User['pk']]),
        ...data,
      },
    });

    if (data.pk === this.currentUserPk) {
      this.rootStore.userStore.loadCurrentUser();
    }

    runInAction(() => {
      this.items = {
        ...this.items,
        [data.pk as User['pk']]: user,
      };
    });
  }

  @action
  async updateCurrentUser(data: Partial<User>) {
    const user = await makeRequest(`/user/`, {
      method: 'PUT',
      data: {
        ...prepareForUpdate(this.items[this.currentUserPk as User['pk']]),
        ...data,
      },
    });

    runInAction(() => {
      this.items = {
        ...this.items,
        [this.currentUserPk as User['pk']]: user,
      };
    });
  }

  @action
  async fetchVerificationCode(userPk: User['pk'], recaptchaToken: string) {
    await makeRequest(`/users/${userPk}/get_verification_code/`, {
      method: 'GET',
      headers: { 'X-OnCall-Recaptcha': recaptchaToken },
    }).catch(throttlingError);
  }

  @action
  async fetchVerificationCall(userPk: User['pk'], recaptchaToken: string) {
    await makeRequest(`/users/${userPk}/get_verification_call/`, {
      method: 'GET',
      headers: { 'X-OnCall-Recaptcha': recaptchaToken },
    }).catch(throttlingError);
  }

  @action
  async verifyPhone(userPk: User['pk'], token: string) {
    return await makeRequest(`/users/${userPk}/verify_number/?token=${token}`, {
      method: 'PUT',
    }).catch(throttlingError);
  }

  @action
  async forgetPhone(userPk: User['pk']) {
    return await makeRequest(`/users/${userPk}/forget_number/`, {
      method: 'PUT',
    });
  }

  @action
  async updateNotificationPolicies(id: User['pk']) {
    const importantEPs = await makeRequest('/notification_policies/', {
      params: { user: id, important: true },
    });

    const nonImportantEPs = await makeRequest('/notification_policies/', {
      params: { user: id, important: false },
    });

    runInAction(() => {
      this.notificationPolicies = {
        ...this.notificationPolicies,
        [id]: [...nonImportantEPs, ...importantEPs],
      };
    });
  }

  @action
  async moveNotificationPolicyToPosition(userPk: User['pk'], oldIndex: number, newIndex: number, offset: number) {
    const notificationPolicy = this.notificationPolicies[userPk][oldIndex + offset];

    this.notificationPolicies[userPk] = move(this.notificationPolicies[userPk], oldIndex + offset, newIndex + offset);

    await makeRequest(`/notification_policies/${notificationPolicy.id}/move_to_position/?position=${newIndex}`, {
      method: 'PUT',
    });

    this.updateNotificationPolicies(userPk);

    this.updateItem(userPk); // to update notification_chain_verbal
  }

  @action
  async addNotificationPolicy(userPk: User['pk'], important: NotificationPolicyType['important']) {
    await makeRequest(`/notification_policies/`, {
      method: 'POST',
      data: { user: userPk, important },
    });

    this.updateNotificationPolicies(userPk);

    this.updateItem(userPk); // to update notification_chain_verbal
  }

  @action
  async updateNotificationPolicy(userPk: User['pk'], id: NotificationPolicyType['id'], value: NotificationPolicyType) {
    this.notificationPolicies = {
      ...this.notificationPolicies,
      [userPk]: this.notificationPolicies[userPk].map((policy: NotificationPolicyType) =>
        id === policy.id ? { ...policy, ...value } : policy
      ),
    };

    const notificationPolicy = await makeRequest(`/notification_policies/${id}/`, {
      method: 'PUT',
      data: value,
    });

    runInAction(() => {
      this.notificationPolicies = {
        ...this.notificationPolicies,
        [userPk]: this.notificationPolicies[userPk].map((policy: NotificationPolicyType) =>
          id === policy.id ? { ...policy, ...notificationPolicy } : policy
        ),
      };
    });

    this.updateItem(userPk); // to update notification_chain_verbal
  }

  @action
  async deleteNotificationPolicy(userPk: User['pk'], id: NotificationPolicyType['id']) {
    await makeRequest(`/notification_policies/${id}`, { method: 'DELETE' }).catch(this.onApiError);

    this.updateNotificationPolicies(userPk);

    this.updateItem(userPk); // to update notification_chain_verbal
  }

  @action.bound
  async updateNotificationPolicyOptions() {
    const response = await makeRequest('/notification_policies/', {
      method: 'OPTIONS',
    });

    runInAction(() => {
      this.notificationChoices = get(response, 'actions.POST', []);
    });
  }

  @action
  async sendTestPushNotification(userId: User['pk'], isCritical: boolean) {
    return await makeRequest(`/users/${userId}/send_test_push`, {
      method: 'POST',
      params: {
        critical: isCritical,
      },
    });
  }

  @action.bound
  async updateNotifyByOptions() {
    const response = await makeRequest('/notification_policies/notify_by_options/', {});

    runInAction(() => {
      this.notifyByOptions = response;
    });
  }

  @action
  async makeTestCall(userPk: User['pk']) {
    this.isTestCallInProgress = true;

    return await makeRequest(`/users/${userPk}/make_test_call/`, {
      method: 'POST',
    })
      .catch(this.onApiError)
      .finally(() => {
        runInAction(() => {
          this.isTestCallInProgress = false;
        });
      });
  }

  async sendTestSms(userPk: User['pk']) {
    this.isTestCallInProgress = true;

    return await makeRequest(`/users/${userPk}/send_test_sms/`, {
      method: 'POST',
    })
      .catch(this.onApiError)
      .finally(() => {
        this.isTestCallInProgress = false;
      });
  }

  async getiCalLink(userPk: User['pk']) {
    return await makeRequest(`/users/${userPk}/export_token/`, {
      method: 'GET',
    });
  }

  async createiCalLink(userPk: User['pk']) {
    return await makeRequest(`/users/${userPk}/export_token/`, {
      method: 'POST',
    });
  }

  async deleteiCalLink(userPk: User['pk']) {
    await makeRequest(`/users/${userPk}/export_token/`, {
      method: 'DELETE',
    });
  }
}
