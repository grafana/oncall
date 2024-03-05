import { config } from '@grafana/runtime';
import dayjs from 'dayjs';
import { get } from 'lodash-es';
import { action, computed, observable, makeObservable, runInAction, makeAutoObservable } from 'mobx';

import { BaseStore } from 'models/base_store';
import { ActionKey } from 'models/loader/action-keys';
import { NotificationPolicyType } from 'models/notification_policy/notification_policy';
import { makeRequest } from 'network/network';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { onCallApi } from 'network/oncall-api/http-client';
import { move } from 'state/helpers';
import { RootStore } from 'state/rootStore';
import { isUserActionAllowed, UserActions } from 'utils/authorization/authorization';
import { AutoLoadingState } from 'utils/decorators';
import { throttlingError } from 'utils/utils';

import { UserHelper } from './user.helpers';
import { User } from './user.types';

export type PaginatedUsersResponse<UT = User> = {
  count: number;
  page_size: number;
  results: UT[];
};

export class UserStore {
  rootStore: RootStore;
  searchResult: { count?: number; results?: Array<User['pk']>; page_size?: number } = {};
  items: { [pk: string]: ApiSchemas['User'] } = {};
  notificationPolicies: any = {};
  notificationChoices: any = [];
  notifyByOptions: any = [];
  currentUserPk?: User['pk'];

  constructor(rootStore: RootStore) {
    makeAutoObservable(this, undefined, { autoBind: true });
    this.rootStore = rootStore;
  }

  async updateItems(f: any = { searchTerm: '' }, page = 1, invalidateFn?: () => boolean): Promise<any> {
    const response = await UserHelper.search(f, page);

    if (invalidateFn && invalidateFn()) {
      return;
    }

    const { count, results, page_size } = response;

    runInAction(() => {
      this.items = {
        ...this.items,
        ...results.reduce(
          (acc: { [key: number]: ApiSchemas['User'] }, item: ApiSchemas['User']) => ({
            ...acc,
            [item.pk]: {
              ...item,
              timezone: UserHelper.getTimezone(item),
            },
          }),
          {}
        ),
      };

      this.searchResult = {
        count,
        page_size,
        results: results.map((item: ApiSchemas['User']) => item.pk),
      };
    });

    return response;
  }

  @AutoLoadingState(ActionKey.FETCH_USERS)
  @action.bound
  async loadUser({
    userPk,
    skipErrorHandling = false,
    shouldDuplicatePendingFetch = true,
  }: {
    userPk: User['pk'];
    skipErrorHandling?: boolean;
    shouldDuplicatePendingFetch?: boolean;
  }) {
    const isAlreadyFetching = this.rootStore.loaderStore.isLoading(ActionKey.FETCH_USERS);

    if (!shouldDuplicatePendingFetch && isAlreadyFetching) {
      return this.items[userPk];
    }

    const { data } = await onCallApi({ skipErrorHandling }).GET('/users/{id}/', { params: { path: { id: userPk } } });

    runInAction(() => {
      this.items = {
        ...this.items,
        [data.pk]: { ...data, timezone: UserHelper.getTimezone(data) },
      };
    });

    return data;
  }

  @action.bound
  async updateItem(userPk: User['pk']) {
    if (this.itemsCurrentlyUpdating[userPk]) {
      return;
    }

    this.itemsCurrentlyUpdating[userPk] = true;

    const user = await this.getById(userPk);

    runInAction(() => {
      this.items = {
        ...this.items,
        [user.pk]: { ...user, timezone: UserHelper.getTimezone(user) },
      };
    });

    delete this.itemsCurrentlyUpdating[userPk];
  }

  @action.bound
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

  @action.bound
  async refreshTimezone(id: User['pk']) {
    const { timezone: grafanaPreferencesTimezone } = config.bootData.user;
    const timezone = grafanaPreferencesTimezone === 'browser' ? dayjs.tz.guess() : grafanaPreferencesTimezone;
    if (isUserActionAllowed(UserActions.UserSettingsWrite)) {
      this.update(id, { timezone });
    }

    this.rootStore.timezoneStore.setSelectedTimezoneOffsetBasedOnTz(timezone);

    return timezone;
  }

  @action.bound
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

  @action.bound
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

  @action.bound
  unlinkBackend = async (userPk: User['pk'], backend: string) => {
    await makeRequest(`/users/${userPk}/unlink_backend/?backend=${backend}`, {
      method: 'POST',
    });

    this.loadCurrentUser();
  };

  @action.bound
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

  @action.bound
  async updateUser(data: Partial<User>) {
    const user = await makeRequest(`/users/${data.pk}/`, {
      method: 'PUT',
      data: {
        ...UserHelper.prepareForUpdate(this.items[data.pk as User['pk']]),
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

  @action.bound
  async updateCurrentUser(data: Partial<User>) {
    const user = await makeRequest(`/user/`, {
      method: 'PUT',
      data: {
        ...UserHelper.prepareForUpdate(this.items[this.currentUserPk as User['pk']]),
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

  @action.bound
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

  @action.bound
  async moveNotificationPolicyToPosition(userPk: User['pk'], oldIndex: number, newIndex: number, offset: number) {
    const notificationPolicy = this.notificationPolicies[userPk][oldIndex + offset];

    this.notificationPolicies[userPk] = move(this.notificationPolicies[userPk], oldIndex + offset, newIndex + offset);

    await makeRequest(`/notification_policies/${notificationPolicy.id}/move_to_position/?position=${newIndex}`, {
      method: 'PUT',
    });

    this.updateNotificationPolicies(userPk);

    this.updateItem(userPk); // to update notification_chain_verbal
  }

  @action.bound
  async addNotificationPolicy(userPk: User['pk'], important: NotificationPolicyType['important']) {
    await makeRequest(`/notification_policies/`, {
      method: 'POST',
      data: { user: userPk, important },
    });

    this.updateNotificationPolicies(userPk);

    this.updateItem(userPk); // to update notification_chain_verbal
  }

  @action.bound
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

  @action.bound
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

  @action.bound
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

  @action.bound
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

  @computed
  get currentUser() {
    if (!this.currentUserPk) {
      return undefined;
    }
    return this.items[this.currentUserPk as User['pk']];
  }
}
