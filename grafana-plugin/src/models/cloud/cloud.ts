import { action, observable } from 'mobx';

import BaseStore from 'models/base_store';
import { makeRequest } from 'network';
import { RootStore } from 'state';

import { Cloud } from './cloud.types';

export class CloudStore extends BaseStore {
  @observable.shallow
  searchResult: { matched_users_count?: number; results?: Array<Cloud['id']> } = {};

  @observable.shallow
  items: { [id: string]: Cloud } = {};

  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/cloud_users/';
  }

  @action
  async updateItems(page = 1) {
    const { matched_users_count, results } = await makeRequest(this.path, {
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
      matched_users_count,
      results: results.map((item: Cloud) => item.id),
    };
  }

  getSearchResult() {
    return {
      matched_users_count: this.searchResult.matched_users_count,
      results: this.searchResult.results && this.searchResult.results.map((id: Cloud['id']) => this.items?.[id]),
    };
  }

  async syncCloudUsers() {
    return await makeRequest(`${this.path}`, { method: 'POST' });
  }

  async syncCloudUser(id: string) {
    return await makeRequest(`${this.path}${id}/sync/`, { method: 'POST' });
  }

  getCloudHeartbeat = async () =>
    await makeRequest(`/cloud_heartbeat/`, { method: 'POST' }).catch((error) => {
      console.log(error);
    });

  async getCloudUser(id: string) {
    return await makeRequest(`${this.path}${id}`, { method: 'GET' });
  }

  getCloudConnectionStatus = async () => await makeRequest(`/cloud_connection/`, { method: 'GET' });

  disconnectToCloud = async () => await makeRequest(`/cloud_connection/`, { method: 'DELETE' });
}
