import { action, observable } from 'mobx';

import BaseStore from 'models/base_store';
import { makeRequest } from 'network';
import { RootStore } from 'state';

import { UserGroup } from './user_group.types';

export class UserGroupStore extends BaseStore {
  @observable.shallow
  searchResult: { [key: string]: Array<UserGroup['id']> } = {};

  @observable.shallow
  items?: { [id: string]: UserGroup[] } = {};

  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/user_groups/';
  }

  @action
  async updateItems(query = '') {
    const result = await makeRequest(`${this.path}`, {
      params: { search: query },
    });

    this.items = {
      ...this.items,
      ...result.reduce(
        (acc: { [key: number]: UserGroup }, item: UserGroup) => ({
          ...acc,
          [item.id]: item,
        }),
        {}
      ),
    };

    this.searchResult = {
      ...(this.searchResult || {}),
      [query]: result.map((item: UserGroup) => item.id),
    };
  }

  getSearchResult(query = '') {
    if (!this.searchResult[query]) {
      return undefined;
    }

    return this.searchResult[query].map((userGroupId: UserGroup['id']) => this.items?.[userGroupId]);
  }
}
