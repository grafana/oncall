import { action, observable } from 'mobx';

import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import BaseStore from 'models/base_store';
import { makeRequest } from 'network';
import { RootStore } from 'state';

import { Heartbeat } from './heartbeat.types';

export class HeartbeatStore extends BaseStore {
  @observable.shallow
  items: { [id: string]: Heartbeat } = {};

  @observable.shallow
  timeoutOptions: any;

  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/heartbeats/';
  }

  @action
  async updateTimeoutOptions() {
    this.timeoutOptions = await makeRequest(`${this.path}timeout_options/`, {});
  }

  @action
  async saveHeartbeat(id: Heartbeat['id'], data: Partial<Heartbeat>) {
    const response = await super.update<Heartbeat>(id, data);

    if (!response) {
      return;
    }

    this.items = {
      ...this.items,
      [response.id]: response,
    };
  }

  @action
  async createHeartbeat(alertReceiveChannelId: AlertReceiveChannel['id'], data: Partial<Heartbeat>) {
    const response = await super.create<Heartbeat>({
      alert_receive_channel: alertReceiveChannelId,
      ...data,
    });

    if (!response) {
      return;
    }

    this.rootStore.alertReceiveChannelStore.alertReceiveChannelToHeartbeat = {
      ...this.rootStore.alertReceiveChannelStore.alertReceiveChannelToHeartbeat,
      [alertReceiveChannelId]: response.id,
    };

    this.items = {
      ...this.items,
      [response.id]: response,
    };
  }
}
