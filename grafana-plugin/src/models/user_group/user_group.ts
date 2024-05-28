import { action, observable, makeObservable, runInAction } from 'mobx';

import { BaseStore } from 'models/base_store';
import { makeRequest } from 'network/network';
import { RootStore } from 'state/rootStore';

import { UserGroup } from './user_group.types';

export class UserGroupStore extends BaseStore {
  @observable.shallow
  searchResult: { [key: string]: Array<UserGroup['id']> } = {};

  @observable.shallow
  items?: { [id: string]: UserGroup } = {};

  constructor(rootStore: RootStore) {
    super(rootStore);

    makeObservable(this);

    this.path = '/user_groups/';
  }

  @action.bound
  async updateItems(query = '', id?: string) {
    const result = await makeRequest(`${this.path}`, {
      params: { search: query, id },
    });

    runInAction(() => {
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
    });
  }

  @action.bound
  async fetchItemById(id: string) {
    const item: UserGroup = await this.getById(id);

    runInAction(() => {
      this.items = {
        ...this.items,
        [id]: item,
      };
    });
  }

  getSearchResult = (query = '') => {
    if (!this.searchResult[query]) {
      return undefined;
    }

    return this.searchResult[query].map((userGroupId: UserGroup['id']) => this.items?.[userGroupId]);
  };
}
