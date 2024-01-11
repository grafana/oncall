import { action, observable, makeObservable, runInAction } from 'mobx';

import BaseStore from 'models/base_store';
import { makeRequest } from 'network';
import { RootStore } from 'state';

import { Cloud } from './cloud.types';

export class CloudStore extends BaseStore {
  @observable.shallow
  searchResult: { matched_users_count?: number; results?: Array<Cloud['id']> } = {};

  @observable.shallow
  items: { [id: string]: Cloud } = {};

  @observable
  cloudConnectionStatus: { cloud_connection_status: boolean } = { cloud_connection_status: false };

  constructor(rootStore: RootStore) {
    super(rootStore);

    makeObservable(this);

    this.path = '/cloud_users/';
  }

  @action.bound
  async updateItems(page = 1) {
    const { matched_users_count, results } = await makeRequest(this.path, {
      params: { page },
    });

    runInAction(() => {
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
    });
  }

  @action.bound
  getSearchResult() {
    return {
      matched_users_count: this.searchResult.matched_users_count,
      results: this.searchResult.results && this.searchResult.results.map((id: Cloud['id']) => this.items?.[id]),
    };
  }

  @action.bound
  async syncCloudUsers() {
    return await makeRequest(`${this.path}`, { method: 'POST' });
  }

  @action.bound
  async syncCloudUser(id: string) {
    return await makeRequest(`${this.path}${id}/sync/`, { method: 'POST' });
  }

  @action.bound
  async getCloudHeartbeat() {
    return await makeRequest(`/cloud_heartbeat/`, { method: 'POST' });
  }

  @action.bound
  async getCloudUser(id: string) {
    return await makeRequest(`${this.path}${id}`, { method: 'GET' });
  }

  @action.bound
  async loadCloudConnectionStatus() {
    const result = await this.getCloudConnectionStatus();

    runInAction(() => {
      this.cloudConnectionStatus = result;
    });
  }

  @action.bound
  async getCloudConnectionStatus() {
    return await makeRequest(`/cloud_connection/`, { method: 'GET' });
  }

  @action.bound
  async disconnectToCloud() {
    return await makeRequest(`/cloud_connection/`, { method: 'DELETE' });
  }
}
