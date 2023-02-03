import { action, observable } from 'mobx';

import BaseStore from 'models/base_store';
import { makeRequest } from 'network';
import { RootStore } from 'state';

import { SlackChannel } from './slack_channel.types';

export class SlackChannelStore extends BaseStore {
  @observable.shallow
  items: { [id: string]: SlackChannel } = {};

  @observable.shallow
  searchResult: { [key: string]: Array<SlackChannel['id']> } = {};

  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/slack_channels/';
  }

  @action // deprecated, use updateItem instead
  async updateById(id: SlackChannel['id']) {
    const response = await this.getById(id);

    this.items = {
      ...this.items,
      [id]: response,
    };
  }

  @action
  async updateItem(id: SlackChannel['id']) {
    const response = await this.getById(id);

    this.items = {
      ...this.items,
      [id]: response,
    };
  }

  @action
  async updateItems(query = '') {
    const { results } = await makeRequest(`${this.path}`, {
      params: { search: query },
    });

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
  }

  getSearchResult(query = '') {
    if (!this.searchResult[query]) {
      return undefined;
    }

    return this.searchResult[query].map((slackChannelId: SlackChannel['id']) => this.items[slackChannelId]);
  }
}
