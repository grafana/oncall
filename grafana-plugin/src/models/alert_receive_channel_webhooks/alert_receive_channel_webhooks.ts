import { keyBy } from 'lodash-es';
import { makeAutoObservable, runInAction } from 'mobx';

import { ApiSchemas } from 'network/oncall-api/api.types';
import { onCallApi } from 'network/oncall-api/http-client';
import { RootBaseStore } from 'state/rootBaseStore/RootBaseStore';
import { WithGlobalNotification } from 'utils/decorators';

export class AlertReceiveChannelWebhooksStore {
  rootStore: RootBaseStore;
  items: Record<ApiSchemas['Webhook']['id'], ApiSchemas['Webhook']> = {};

  constructor(rootStore: RootBaseStore) {
    makeAutoObservable(this, undefined, { autoBind: true });
    this.rootStore = rootStore;
  }

  async fetchItems(integrationId: ApiSchemas['AlertReceiveChannel']['id']) {
    const { data } = await onCallApi().GET('/alert_receive_channels/{id}/webhooks/', {
      params: { path: { id: integrationId } },
    });
    runInAction(() => {
      this.items = keyBy(data, 'id');
    });
  }

  @WithGlobalNotification({
    success: 'Webhook has been created.',
    failure: 'There was an issue creating new webhook. Please try again.',
  })
  async create(integrationId: ApiSchemas['AlertReceiveChannel']['id'], webhook: Partial<ApiSchemas['Webhook']>) {
    const { data } = await onCallApi().POST('/alert_receive_channels/{id}/webhooks/', {
      params: { path: { id: integrationId } },
      body: webhook as ApiSchemas['Webhook'],
    });
    runInAction(() => {
      this.items[data.id] = data;
    });
  }

  @WithGlobalNotification({
    success: 'Webhook has been updated.',
    failure: 'There was an issue updating a webhook. Please try again.',
  })
  async update(integrationId: ApiSchemas['AlertReceiveChannel']['id'], webhook: Partial<ApiSchemas['Webhook']>) {
    const { data } = await onCallApi().PUT('/alert_receive_channels/{id}/webhooks/{webhook_id}/', {
      params: { path: { id: integrationId, webhook_id: webhook.id } },
      body: webhook as ApiSchemas['Webhook'],
    });
    runInAction(() => {
      this.items[data.id] = data;
    });
  }

  @WithGlobalNotification({
    success: 'Webhook has been deleted.',
    failure: 'There was an issue deleting a webhook. Please try again.',
  })
  async delete(integrationId: ApiSchemas['AlertReceiveChannel']['id'], webhookId: ApiSchemas['Webhook']['id']) {
    await onCallApi().DELETE('/alert_receive_channels/{id}/webhooks/{webhook_id}/', {
      params: { path: { id: integrationId, webhook_id: webhookId } },
    });
    runInAction(() => {
      delete this.items[webhookId];
    });
  }
}
