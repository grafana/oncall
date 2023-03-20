import { action, observable } from 'mobx';

import BaseStore from 'models/base_store';
import { makeRequest } from 'network';
import { RootStore } from 'state';

import { OutgoingWebhook } from './outgoing_webhook.types';

export class OutgoingWebhookStore extends BaseStore {
  @observable.shallow
  items: { [id: string]: OutgoingWebhook } = {};

  @observable.shallow
  searchResult: { [key: string]: Array<OutgoingWebhook['id']> } = {};

  @observable
  incidentFilters: any;

  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/custom_buttons/';
  }

  @action
  async loadItem(id: OutgoingWebhook['id'], skipErrorHandling = false): Promise<OutgoingWebhook> {
    const outgoingWebhook = await this.getById(id, skipErrorHandling);

    this.items = {
      ...this.items,
      [id]: outgoingWebhook,
    };

    return outgoingWebhook;
  }

  @action
  async updateById(id: OutgoingWebhook['id']) {
    const response = await this.getById(id);

    this.items = {
      ...this.items,
      [id]: response,
    };
  }

  @action
  async updateItem(id: OutgoingWebhook['id'], fromOrganization = false) {
    let outgoingWebhook;

    try {
      outgoingWebhook = await this.getById(id, true, fromOrganization);
    } catch (error) {
      if (error.response.data.error_code === 'wrong_team') {
        outgoingWebhook = {
          id,
          name: '🔒 Private outgoing webhook',
          private: true,
        };
      }
    }

    if (outgoingWebhook) {
      this.items = {
        ...this.items,
        [id]: outgoingWebhook,
      };
    }
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
        (acc: { [key: number]: OutgoingWebhook }, item: OutgoingWebhook) => ({
          ...acc,
          [item.id]: item,
        }),
        {}
      ),
    };

    const key = typeof query === 'string' ? query : '';

    this.searchResult = {
      ...this.searchResult,
      [key]: results.map((item: OutgoingWebhook) => item.id),
    };
  }

  @action
  async updateOutgoingWebhooksFilters(params: any) {
    this.incidentFilters = params;

    this.updateItems();
  }

  getSearchResult(query = '') {
    if (!this.searchResult[query]) {
      return undefined;
    }

    return this.searchResult[query].map((outgoingWebhookId: OutgoingWebhook['id']) => this.items[outgoingWebhookId]);
  }
}
