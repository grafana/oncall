import { action, observable } from 'mobx';

import BaseStore from 'models/base_store';
import { makeRequest } from 'network';
import { RootStore } from 'state';

import { OutgoingWebhook2 } from './outgoing_webhook_2.types';

export class OutgoingWebhook2Store extends BaseStore {
  @observable.shallow
  items: { [id: string]: OutgoingWebhook2 } = {};

  @observable.shallow
  searchResult: { [key: string]: Array<OutgoingWebhook2['id']> } = {};

  @observable
  incidentFilters: any;

  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/webhooks/';
  }

  @action
  async loadItem(id: OutgoingWebhook2['id'], skipErrorHandling = false): Promise<OutgoingWebhook2> {
    const outgoingWebhook2 = await this.getById(id, skipErrorHandling);

    this.items = {
      ...this.items,
      [id]: outgoingWebhook2,
    };

    return outgoingWebhook2;
  }

  @action
  async updateById(id: OutgoingWebhook2['id']) {
    const response = await this.getById(id);

    this.items = {
      ...this.items,
      [id]: response,
    };
  }

  @action
  async updateItem(id: OutgoingWebhook2['id'], fromOrganization = false) {
    const response = await this.getById(id, false, fromOrganization);
    this.items = {
      ...this.items,
      [id]: response,
    };
  }

  @action
  async updateItems(query: any = '') {
    const params = typeof query === 'string' ? { search: query } : query;

    const results = await makeRequest(`${this.path}`, {
      params,
    });

    this.items = {
      ...this.items,
      ...results.reduce(
        (acc: { [key: number]: OutgoingWebhook2 }, item: OutgoingWebhook2) => ({
          ...acc,
          [item.id]: item,
        }),
        {}
      ),
    };

    const key = typeof query === 'string' ? query : '';

    this.searchResult = {
      ...this.searchResult,
      [key]: results.map((item: OutgoingWebhook2) => item.id),
    };
  }

  @action
  async updateOutgoingWebhooks2Filters(params: any) {
    this.incidentFilters = params;

    this.updateItems();
  }

  getSearchResult(query = '') {
    if (!this.searchResult[query]) {
      return undefined;
    }

    return this.searchResult[query].map((outgoingWebhook2Id: OutgoingWebhook2['id']) => this.items[outgoingWebhook2Id]);
  }
}
