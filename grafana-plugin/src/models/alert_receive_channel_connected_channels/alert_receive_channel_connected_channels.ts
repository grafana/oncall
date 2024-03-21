import { keyBy } from 'lodash-es';
import { makeAutoObservable, runInAction } from 'mobx';

import { ActionKey } from 'models/loader/action-keys';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { onCallApi } from 'network/oncall-api/http-client';
import { RootBaseStore } from 'state/rootBaseStore/RootBaseStore';
import { AutoLoadingState } from 'utils/decorators';

export class AlertReceiveChannelConnectedChannelsStore {
  rootStore: RootBaseStore;
  items: Record<string, ApiSchemas['AlertReceiveChannelConnectedChannel']> = {};

  constructor(rootStore: RootBaseStore) {
    makeAutoObservable(this, undefined, { autoBind: true });
    this.rootStore = rootStore;
  }

  get itemsAsList() {
    return Object.values(this.items).filter(({ alert_receive_channel: { deleted } }) => !deleted);
  }

  @AutoLoadingState(ActionKey.FETCH_INTEGRATION_CHANNELS)
  async fetchItems(integrationId: string) {
    const { data } = await onCallApi().GET('/alert_receive_channels/{id}/connected_alert_receive_channels/', {
      params: { path: { id: integrationId } },
    });
    runInAction(() => {
      this.items = keyBy(
        data.connected_alert_receive_channels,
        ({ alert_receive_channel }) => alert_receive_channel.id
      );
    });
  }

  @AutoLoadingState(ActionKey.FETCH_INTEGRATIONS_AVAILABLE_FOR_CONNECTION)
  async fetchItemsAvailableForConnection({
    search,
    page,
    currentIntegrationId,
  }: {
    search?: string;
    page: number;
    currentIntegrationId: string;
  }) {
    await this.rootStore.alertReceiveChannelStore.fetchPaginatedItems({
      filters: {
        search,
        id_ne: [...this.itemsAsList.map(({ alert_receive_channel: { id } }) => id), currentIntegrationId],
      },
      perpage: 10,
      page,
    });
  }

  @AutoLoadingState(ActionKey.CONNECT_INTEGRATION_CHANNELS)
  async connectChannels(
    integrationId: ApiSchemas['AlertReceiveChannel']['id'],
    channels: Array<ApiSchemas['AlertReceiveChannelNewConnection']>
  ) {
    const { data } = await onCallApi().POST('/alert_receive_channels/{id}/connected_alert_receive_channels/', {
      params: { path: { id: integrationId } },
      body: channels,
    });
    runInAction(() => {
      this.items = keyBy(
        data.connected_alert_receive_channels,
        ({ alert_receive_channel }) => alert_receive_channel.id
      );
    });
  }

  async deleteConnectedChannel({
    sourceIntegrationId,
    connectedIntegrationId,
  }: {
    sourceIntegrationId: string;
    connectedIntegrationId: string;
  }) {
    await onCallApi().DELETE(
      '/alert_receive_channels/{id}/connected_alert_receive_channels/{connected_alert_receive_channel_id}/',
      {
        params: { path: { id: sourceIntegrationId, connected_alert_receive_channel_id: connectedIntegrationId } },
      }
    );
    runInAction(() => {
      delete this.items[connectedIntegrationId];
    });
  }

  async toggleBacksync({
    sourceIntegrationId,
    connectedChannelId,
    backsync,
  }: {
    sourceIntegrationId: string;
    connectedChannelId: string;
    backsync: boolean;
  }) {
    const { data } = await onCallApi().PUT(
      '/alert_receive_channels/{id}/connected_alert_receive_channels/{connected_alert_receive_channel_id}/',
      {
        params: { path: { id: sourceIntegrationId, connected_alert_receive_channel_id: connectedChannelId } },
        body: { backsync } as ApiSchemas['AlertReceiveChannelConnectedChannel'],
      }
    );
    runInAction(() => {
      this.items[data.alert_receive_channel.id] = data;
    });
  }
}
