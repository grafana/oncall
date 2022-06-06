import { get } from 'lodash-es';
import { action, computed, observable } from 'mobx';

import BaseStore from 'models/base_store';
import { NotificationPolicyType } from 'models/notification_policy';
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
  async updateItems(f: any = { searchTerm: '' }, page = 1) {
    const filters = typeof f === 'string' ? { searchTerm: f } : f; // for GSelect compatibility
    const { searchTerm: search } = filters;
    const { count, results } = await makeRequest(this.path, {
      params: { search, page },
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
      results:
        this.searchResult.results &&
        this.searchResult.results.map((cloud_user_id: Cloud['id']) => this.items?.[cloud_user_id]),
    };
  }

  async syncCloudUsers() {
    return await makeRequest(`${this.path}sync_with_cloud`, { method: 'POST' });
  }

  async getCloudConnectionStatus() {
    return await makeRequest(`/cloud_connection/`, { method: 'GET' });
  }

  @action
  async connectToCloud(token: string) {
    return await makeRequest(`/live_settings/`, { method: 'PUT', params: { token } });
  }

  @action
  async disconnectToCloud() {
    return await makeRequest(`/live_settings/`, { method: 'DELETE' });
  }
}
