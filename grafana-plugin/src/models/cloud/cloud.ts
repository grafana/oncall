import { get } from 'lodash-es';
import { action, computed, observable } from 'mobx';

import BaseStore from 'models/base_store';
import { NotificationPolicyType } from 'models/notification_policy';
import { User } from 'models/user/user.types';
import { makeRequest } from 'network';
import { Mixpanel } from 'services/mixpanel';
import { RootStore } from 'state';
import { move } from 'state/helpers';

import { Cloud } from './cloud.types';

export class CloudStore extends BaseStore {
  @observable.shallow
  searchResult: { count?: number; results?: Array<Cloud['id']> } = {};

  @observable.shallow
  items: { [id: string]: Cloud } = {};

  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/cloud_users/';
  }

  @action
  async updateItems(page = 1) {
    const { count, results } = await makeRequest(this.path, {
      params: { page },
    });

    this.items = {
      ...this.items,
      ...results.reduce(
        (acc: { [key: number]: Cloud }, item: Cloud) => ({
          ...acc,
          [item.id]: item,
        }),
        {}
      ),
    };

    this.searchResult = {
      count,
      results: results.map((item: Cloud) => item.id),
    };
  }

  getSearchResult() {
    return {
      count: this.searchResult.count,
      results: this.searchResult.results && this.searchResult.results.map((id: Cloud['id']) => this.items?.[id]),
    };
  }

  async syncCloudUsers() {
    return await makeRequest(`${this.path}`, { method: 'POST' });
  }

  async syncCloudUser(id: string) {
    return await makeRequest(`${this.path}${id}/sync/`, { method: 'POST' });
  }

  async getCloudConnectionStatus() {
    return await makeRequest(`/cloud_connection/`, { method: 'GET' });
  }

  @action
  async disconnectToCloud() {
    return await makeRequest(`/cloud_connection/`, { method: 'DELETE' });
  }
}
