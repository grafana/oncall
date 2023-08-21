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

  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/webhooks/';
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

  getSearchResult(query = '') {
    if (!this.searchResult[query]) {
      return undefined;
    }

    return this.searchResult[query].map((outgoingWebhookId: OutgoingWebhook['id']) => this.items[outgoingWebhookId]);
  }

  async getLastResponses(id: OutgoingWebhook['id']) {
    const result = await makeRequest(`${this.path}${id}/responses`, {});

    return result;
  }

  async renderPreview(id: OutgoingWebhook['id'], template_name: string, template_body: string, payload) {
    return await makeRequest(`${this.path}${id}/preview_template/`, {
      method: 'POST',
      data: { template_name, template_body, payload },
    });
  }
}
