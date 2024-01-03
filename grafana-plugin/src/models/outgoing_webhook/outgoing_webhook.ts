import { action, observable, makeObservable, runInAction } from 'mobx';

import BaseStore from 'models/base_store';
import { LabelsErrors } from 'models/label/label.types';
import { makeRequest } from 'network';
import { RootStore } from 'state';

import { OutgoingWebhook, OutgoingWebhookPreset } from './outgoing_webhook.types';

export class OutgoingWebhookStore extends BaseStore {
  @observable.shallow
  items: { [id: string]: OutgoingWebhook } = {};

  @observable.shallow
  searchResult: { [key: string]: Array<OutgoingWebhook['id']> } = {};

  @observable.shallow
  outgoingWebhookPresets: OutgoingWebhookPreset[] = [];

  @observable
  labelsFormErrors?: LabelsErrors;

  constructor(rootStore: RootStore) {
    super(rootStore);

    makeObservable(this);

    this.path = '/webhooks/';
  }

  @action
  async loadItem(id: OutgoingWebhook['id'], skipErrorHandling = false): Promise<OutgoingWebhook> {
    const outgoingWebhook = await this.getById(id, skipErrorHandling);

    runInAction(() => {
      this.items = {
        ...this.items,
        [id]: outgoingWebhook,
      };
    });

    return outgoingWebhook;
  }

  @action
  async updateById(id: OutgoingWebhook['id']) {
    const response = await this.getById(id);

    runInAction(() => {
      this.items = {
        ...this.items,
        [id]: response,
      };
    });
  }

  @action
  async updateItem(id: OutgoingWebhook['id'], fromOrganization = false) {
    const response = await this.getById(id, false, fromOrganization);

    runInAction(() => {
      this.items = {
        ...this.items,
        [id]: response,
      };
    });
  }

  @action
  async updateItems(query: any = '') {
    const params = typeof query === 'string' ? { search: query } : query;

    const results = await makeRequest(`${this.path}`, {
      params,
    });

    runInAction(() => {
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
    });
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

  @action.bound
  async updateOutgoingWebhookPresetsOptions() {
    const response = await makeRequest(`/webhooks/preset_options/`, {});

    runInAction(() => {
      this.outgoingWebhookPresets = response;
    });
  }

  @action.bound
  setLabelsFormErrors(errors: LabelsErrors) {
    this.labelsFormErrors = errors;
  }
}
