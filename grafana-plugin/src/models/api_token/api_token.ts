import { action, observable } from 'mobx';

import BaseStore from 'models/base_store';
import { makeRequest } from 'network';
import { Mixpanel } from 'services/mixpanel';
import { RootStore } from 'state';

import { ApiToken } from './api_token.types';

export class ApiTokenStore extends BaseStore {
  @observable.shallow
  items: { [id: number]: ApiToken } = {};

  @observable.shallow
  searchResult: { [key: string]: Array<ApiToken['id']> } = {};

  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/tokens/';
  }

  @action
  async updateItems(query = '') {
    const results = await makeRequest(`${this.path}`, {
      params: { search: query },
    });

    this.items = {
      ...this.items,
      ...results.reduce(
        (acc: { [key: number]: ApiToken }, item: ApiToken) => ({
          ...acc,
          [item.id]: item,
        }),
        {}
      ),
    };

    this.searchResult = {
      ...this.searchResult,
      [query]: results.map((item: ApiToken) => item.id),
    };
  }

  getSearchResult(query = '') {
    if (!this.searchResult[query]) {
      return undefined;
    }

    return this.searchResult[query].map((apiTokenId: ApiToken['id']) => this.items[apiTokenId]);
  }

  async revokeApiToken(id: ApiToken['id']) {
    Mixpanel.track('Revoke ApiToken', null);

    return await makeRequest(`${this.path}${id}/`, {
      method: 'DELETE',
    });
  }
}
