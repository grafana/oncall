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

  @AutoLoadingState(ActionKey.FETCH_INTEGRATION_CHANNELS)
  async fetchItems(integrationId: string) {
    const { data } = await onCallApi().GET('/alert_receive_channels/{id}/connected_channels/', {
      params: { path: { id: integrationId } },
    });
    runInAction(() => {
      this.items = keyBy(
        data.connected_alert_receive_channels,
        ({ alert_receive_channel }) => alert_receive_channel.id
      );
    });
  }

  @AutoLoadingState(ActionKey.CONNECT_INTEGRATION_CHANNELS)
  async connectChannels(
    integrationId: ApiSchemas['AlertReceiveChannel']['id'],
    channels: ApiSchemas['AlertReceiveChannelNewConnection']
  ) {
    const { data } = await onCallApi().POST('/alert_receive_channels/{id}/connected_channels/', {
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
}
