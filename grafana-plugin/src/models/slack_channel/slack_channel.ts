import { action, observable, makeObservable, runInAction } from 'mobx';

import { BaseStore } from 'models/base_store';
import { makeRequest } from 'network/network';
import { RootStore } from 'state/rootStore';

import { SlackChannel } from './slack_channel.types';

export class SlackChannelStore extends BaseStore {
  @observable.shallow
  items: { [id: string]: SlackChannel } = {};

  @observable.shallow
  searchResult: { [key: string]: Array<SlackChannel['id']> } = {};

  constructor(rootStore: RootStore) {
    super(rootStore);

    makeObservable(this);

    this.path = '/slack_channels/';
  }

  @action.bound // deprecated, use updateItem instead
  async updateById(id: SlackChannel['id']) {
    const response = await this.getById(id);

    runInAction(() => {
      this.items = {
        ...this.items,
        [id]: response,
      };
    });
  }

  @action.bound
  async updateItem(id: SlackChannel['id']) {
    const response = await this.getById(id);

    runInAction(() => {
      this.items = {
        ...this.items,
        [id]: response,
      };
    });
  }

  @action.bound
  async updateItems(query = '') {
    const { results } = await makeRequest(`${this.path}`, {
      params: { search: query },
    });

    runInAction(() => {
      this.items = {
        ...this.items,
        ...results.reduce(
          (acc: { [key: number]: SlackChannel }, item: SlackChannel) => ({
            ...acc,
            [item.id]: item,
          }),
          {}
        ),
      };

      this.searchResult = {
        ...this.searchResult,
        [query]: results.map((item: SlackChannel) => item.id),
      };
    });
  }

  getSearchResult = (query = '') => {
    if (!this.searchResult[query]) {
      return undefined;
    }

    return this.searchResult[query].map((slackChannelId: SlackChannel['id']) => this.items[slackChannelId]);
  };
}
