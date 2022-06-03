import { action, observable } from 'mobx';

import BaseStore from 'models/base_store';
import { makeRequest } from 'network';
import { RootStore } from 'state';

import { OrganizationLog } from './organization_log.types';

export class OrganizationLogStore extends BaseStore {
  @observable.shallow
  items: { [id: string]: OrganizationLog } = {};

  @observable.shallow
  searchResult?: {
    total: number;
    page: number;
    results: Array<OrganizationLog['id']>;
  };

  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/organization_logs/';
  }

  @action
  async updateItems(query = '', page: number, filters?: any) {
    const { results, count } = await makeRequest(`${this.path}`, {
      params: { search: query, page, ...filters },
    });

    this.items = {
      ...this.items,
      ...results.reduce(
        (acc: { [key: string]: OrganizationLog }, item: OrganizationLog) => ({
          ...acc,
          [item.id]: item,
        }),
        {}
      ),
    };

    this.searchResult = {
      total: count,
      page,
      results: results.map((item: OrganizationLog) => item.id),
    };
  }

  getSearchResult() {
    if (!this.searchResult) {
      return undefined;
    }

    return {
      ...this.searchResult,
      results: this.searchResult.results.map((id: OrganizationLog['id']) => this.items[id]),
    };
  }
}
