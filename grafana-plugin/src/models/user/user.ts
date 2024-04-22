import { config } from '@grafana/runtime';
import dayjs from 'dayjs';
import { get } from 'lodash-es';
import { action, computed, runInAction, makeAutoObservable } from 'mobx';

import { ActionKey } from 'models/loader/action-keys';
import { NotificationPolicyType } from 'models/notification_policy/notification_policy';
import { makeRequest } from 'network/network';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { onCallApi } from 'network/oncall-api/http-client';
import { move } from 'state/helpers';
import { RootStore } from 'state/rootStore';
import { isUserActionAllowed, UserActions } from 'utils/authorization/authorization';
import { AutoLoadingState } from 'utils/decorators';

import { UserHelper } from './user.helpers';

export type PaginatedUsersResponse<UT = ApiSchemas['User']> = {
  count: number;
  page_size: number;
  results: UT[];
};

export class UserStore {
  rootStore: RootStore;
  searchResult: { count?: number; results?: Array<ApiSchemas['User']['pk']>; page_size?: number } = {};
  items: { [pk: string]: ApiSchemas['User'] } = {};
  notificationPolicies: any = {};
  notificationChoices: any = [];
  notifyByOptions: any = [];
  currentUserPk?: ApiSchemas['User']['pk'];
  usersCurrentlyBeingFetched: { [pk: string]: boolean } = {};

  constructor(rootStore: RootStore) {
    makeAutoObservable(this, undefined, { autoBind: true });
    this.rootStore = rootStore;
  }

  async fetchItems(f: any = { searchTerm: '' }, page = 1, invalidateFn?: () => boolean): Promise<any> {
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
              ...this.items[item.pk],
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

  @action.bound
  async fetchItemById({
    userPk,
    skipErrorHandling = false,
    skipIfAlreadyPending = false,
  }: {
    userPk: ApiSchemas['User']['pk'];
    skipErrorHandling?: boolean;
    skipIfAlreadyPending?: boolean;
  }) {
    if (skipIfAlreadyPending && this.usersCurrentlyBeingFetched[userPk]) {
      return this.items[userPk];
    }

    this.usersCurrentlyBeingFetched[userPk] = true;

    const { data } = await onCallApi({ skipErrorHandling }).GET('/users/{id}/', { params: { path: { id: userPk } } });

    runInAction(() => {
      this.items = {
        ...this.items,
        [data.pk]: { ...data, timezone: UserHelper.getTimezone(data) },
      };
      delete this.usersCurrentlyBeingFetched[userPk];
    });

    return data;
  }

  async loadCurrentUser() {
    const response = await makeRequest<ApiSchemas['User']>('/user/', {});
    const timezone = await this.refreshTimezoneIfNeeded(response);

    runInAction(() => {
      this.items = {
        ...this.items,
        [response.pk]: { ...response, timezone },
      };
      this.currentUserPk = response.pk;
    });
  }

  async refreshTimezoneIfNeeded(user: ApiSchemas['User']) {
    const { timezone: grafanaPreferencesTimezone } = config.bootData.user;
    const timezone = grafanaPreferencesTimezone === 'browser' ? dayjs.tz.guess() : grafanaPreferencesTimezone;

    if (user.timezone !== timezone && isUserActionAllowed(UserActions.UserSettingsWrite)) {
      await onCallApi().PUT('/users/{id}/', {
        params: { path: { id: user.pk } },
        body: { timezone } as ApiSchemas['User'],
      });
    }

    this.rootStore.timezoneStore.setSelectedTimezoneOffsetBasedOnTz(timezone);

    return timezone;
  }

  async unlinkSlack(userPk: ApiSchemas['User']['pk']) {
    await onCallApi().POST('/users/{id}/unlink_slack/', { params: { path: { id: userPk } } });
    await this.fetchItemById({ userPk });
  }

  async unlinkTelegram(userPk: ApiSchemas['User']['pk']) {
    await onCallApi().POST('/users/{id}/unlink_telegram/', { params: { path: { id: userPk } } });
    await this.fetchItemById({ userPk });
  }

  async unlinkBackend(userPk: ApiSchemas['User']['pk'], backend: string) {
    await onCallApi().POST('/users/{id}/unlink_backend/', { params: { path: { id: userPk }, query: { backend } } });
    this.loadCurrentUser();
  }

  async disconnectGoogle() {
    await onCallApi().GET('/disconnect/{backend}', { params: { path: { backend: 'google-oauth2' } } });

    this.loadCurrentUser();
  }

  async updateUser(data: Partial<ApiSchemas['User']>) {
    const user = (
      await onCallApi().PUT('/users/{id}/', {
        params: { path: { id: data.pk } },
        body: {
          ...UserHelper.prepareForUpdate(this.items[data.pk]),
          ...data,
        } as ApiSchemas['User'],
      })
    ).data;

    if (data.pk === this.currentUserPk) {
      this.rootStore.userStore.loadCurrentUser();
    }

    runInAction(() => {
      this.items = {
        ...this.items,
        [data.pk]: user,
      };
    });
  }

  async updateCurrentUser(data: Partial<ApiSchemas['User']>) {
    const user = await makeRequest(`/user/`, {
      method: 'PUT',
      data: {
        ...UserHelper.prepareForUpdate(this.items[this.currentUserPk]),
        ...data,
      },
    });

    runInAction(() => {
      this.items = {
        ...this.items,
        [this.currentUserPk]: user,
      };
    });
  }

  async updateNotificationPolicies(id: ApiSchemas['User']['pk']) {
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

  async moveNotificationPolicyToPosition(
    userPk: ApiSchemas['User']['pk'],
    oldIndex: number,
    newIndex: number,
    offset: number
  ) {
    const notificationPolicy = this.notificationPolicies[userPk][oldIndex + offset];
    this.notificationPolicies[userPk] = move(this.notificationPolicies[userPk], oldIndex + offset, newIndex + offset);
    await makeRequest(`/notification_policies/${notificationPolicy.id}/move_to_position/?position=${newIndex}`, {
      method: 'PUT',
    });
    this.updateNotificationPolicies(userPk);
    this.fetchItemById({ userPk }); // to update notification_chain_verbal
  }

  async addNotificationPolicy(userPk: ApiSchemas['User']['pk'], important: NotificationPolicyType['important']) {
    await makeRequest(`/notification_policies/`, {
      method: 'POST',
      data: { user: userPk, important },
    });
    this.updateNotificationPolicies(userPk);
    this.fetchItemById({ userPk }); // to update notification_chain_verbal
  }

  async updateNotificationPolicy(
    userPk: ApiSchemas['User']['pk'],
    id: NotificationPolicyType['id'],
    value: NotificationPolicyType
  ) {
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

    this.fetchItemById({ userPk }); // to update notification_chain_verbal
  }

  async deleteNotificationPolicy(userPk: ApiSchemas['User']['pk'], id: NotificationPolicyType['id']) {
    await makeRequest(`/notification_policies/${id}`, { method: 'DELETE' });
    this.updateNotificationPolicies(userPk);
    this.fetchItemById({ userPk }); // to update notification_chain_verbal
  }

  async updateNotificationPolicyOptions() {
    const response = await makeRequest('/notification_policies/', {
      method: 'OPTIONS',
    });
    runInAction(() => {
      this.notificationChoices = get(response, 'actions.POST', []);
    });
  }

  @action.bound
  async updateNotifyByOptions() {
    const response = await makeRequest('/notification_policies/notify_by_options/', {});

    runInAction(() => {
      this.notifyByOptions = response;
    });
  }

  @AutoLoadingState(ActionKey.TEST_CALL_OR_SMS)
  async makeTestCall(userPk: ApiSchemas['User']['pk']) {
    return (await onCallApi().POST('/users/{id}/make_test_call/', { params: { path: { id: userPk } } })).data;
  }

  @AutoLoadingState(ActionKey.TEST_CALL_OR_SMS)
  async sendTestSms(userPk: ApiSchemas['User']['pk']) {
    return (await onCallApi().POST('/users/{id}/send_test_sms/', { params: { path: { id: userPk } } })).data;
  }

  @computed
  get currentUser() {
    if (!this.currentUserPk) {
      return undefined;
    }
    return this.items[this.currentUserPk];
  }
}
