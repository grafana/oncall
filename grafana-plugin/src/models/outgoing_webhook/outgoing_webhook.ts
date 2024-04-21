import { action, observable, makeObservable, runInAction } from 'mobx';

import { BaseStore } from 'models/base_store';
import { makeRequest } from 'network/network';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { RootStore } from 'state/rootStore';

import { OutgoingWebhookPreset } from './outgoing_webhook.types';

export class OutgoingWebhookStore extends BaseStore {
  @observable.shallow
  items: { [id: string]: ApiSchemas['Webhook'] } = {};

  @observable.shallow
  searchResult: { [key: string]: Array<ApiSchemas['Webhook']['id']> } = {};

  @observable.shallow
  outgoingWebhookPresets: OutgoingWebhookPreset[] = [];

  constructor(rootStore: RootStore) {
    super(rootStore);

    makeObservable(this);

    this.path = '/webhooks/';
  }

  @action.bound
  async loadItem(id: ApiSchemas['Webhook']['id'], skipErrorHandling = false): Promise<ApiSchemas['Webhook']> {
    const outgoingWebhook = await this.getById(id, skipErrorHandling);

    runInAction(() => {
      this.items = {
        ...this.items,
        [id]: outgoingWebhook,
      };
    });

    return outgoingWebhook;
  }

  @action.bound
  async updateById(id: ApiSchemas['Webhook']['id']) {
    const response = await this.getById(id);

    runInAction(() => {
      this.items = {
        ...this.items,
        [id]: response,
      };
    });
  }

  @action.bound
  async updateItem(id: ApiSchemas['Webhook']['id'], fromOrganization = false) {
    const response = await this.getById(id, false, fromOrganization);

    runInAction(() => {
      this.items = {
        ...this.items,
        [id]: response,
      };
    });
  }

  @action.bound
  async updateItems(query: any = '') {
    const params = typeof query === 'string' ? { search: query } : query;

    const results = await makeRequest(`${this.path}`, {
      params,
    });

    runInAction(() => {
      this.items = {
        ...this.items,
        ...results.reduce(
          (acc: { [key: number]: ApiSchemas['Webhook'] }, item: ApiSchemas['Webhook']) => ({
            ...acc,
            [item.id]: item,
          }),
          {}
        ),
      };

      const key = typeof query === 'string' ? query : '';

      this.searchResult = {
        ...this.searchResult,
        [key]: results.map((item: ApiSchemas['Webhook']) => item.id),
      };
    });
  }

  getSearchResult = (query = '') => {
    if (!this.searchResult[query]) {
      return undefined;
    }

    return this.searchResult[query].map(
      (outgoingWebhookId: ApiSchemas['Webhook']['id']) => this.items[outgoingWebhookId]
    );
  };

  async getLastResponses(id: ApiSchemas['Webhook']['id']) {
    const result = await makeRequest(`${this.path}${id}/responses`, {});

    return result;
  }

  async renderPreview(id: ApiSchemas['Webhook']['id'], template_name: string, template_body: string, payload) {
    return await makeRequest(`${this.path}${id}/preview_template/`, {
      method: 'POST',
      data: { template_name, template_body, payload },
    });
  }

  @action.bound
  async updateOutgoingWebhookPresetsOptions() {
    const response = await makeRequest(`/webhooks/preset_options/`, {});

    runInAction(() => {
      this.outgoingWebhookPresets = response;
    });
  }
}
