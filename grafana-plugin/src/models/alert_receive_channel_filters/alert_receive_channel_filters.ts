import { action, observable } from 'mobx';

import BaseStore from 'models/base_store';
import { makeRequest } from 'network';
import { RootStore } from 'state';
import { SelectOption } from 'state/types';

export class AlertReceiveChannelFiltersStore extends BaseStore {
  @observable.shallow
  searchResult: Array<SelectOption['value']>;

  @observable.shallow
  items: { [id: string]: SelectOption } = {};

  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/alert_receive_channels/';
  }

  getSearchResult() {
    if (!this.searchResult) {
      return undefined;
    }

    return this.searchResult.map((value: SelectOption['value']) => this.items?.[value]);
  }

  @action
  async updateItems(query = '') {
    const results = await makeRequest(`${this.path}`, {
      params: { search: query, filters: true },
    });

    this.items = {
      ...this.items,
      ...results.reduce(
        (acc: { [key: string]: SelectOption }, item: SelectOption) => ({
          ...acc,
          [item.value]: item,
        }),
        {}
      ),
    };

    this.searchResult = results.map((item: SelectOption) => item.value);
  }
}
