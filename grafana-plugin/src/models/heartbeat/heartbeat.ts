import { action, observable, makeObservable, runInAction } from 'mobx';

import { BaseStore } from 'models/base_store';
import { makeRequest } from 'network/network';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { RootStore } from 'state/rootStore';

import { Heartbeat } from './heartbeat.types';

export class HeartbeatStore extends BaseStore {
  @observable.shallow
  items: { [id: string]: Heartbeat } = {};

  @observable.shallow
  timeoutOptions: any;

  constructor(rootStore: RootStore) {
    super(rootStore);

    makeObservable(this);

    this.path = '/heartbeats/';
  }

  @action.bound
  async updateTimeoutOptions() {
    const result = await makeRequest(`${this.path}timeout_options/`, {});

    runInAction(() => {
      this.timeoutOptions = result;
    });
  }

  @action.bound
  async saveHeartbeat(id: Heartbeat['id'], data: Partial<Heartbeat>) {
    const response = await super.update<Heartbeat>(id, data);

    if (!response) {
      return;
    }

    runInAction(() => {
      this.items = {
        ...this.items,
        [response.id]: response,
      };
    });
  }

  @action.bound
  async createHeartbeat(alertReceiveChannelId: ApiSchemas['AlertReceiveChannel']['id'], data: Partial<Heartbeat>) {
    const response = await super.create<Heartbeat>({
      alert_receive_channel: alertReceiveChannelId,
      ...data,
    });

    if (!response) {
      return;
    }

    runInAction(() => {
      this.rootStore.alertReceiveChannelStore.alertReceiveChannelToHeartbeat = {
        ...this.rootStore.alertReceiveChannelStore.alertReceiveChannelToHeartbeat,
        [alertReceiveChannelId]: response.id,
      };

      this.items = {
        ...this.items,
        [response.id]: response,
      };
    });
  }
}
