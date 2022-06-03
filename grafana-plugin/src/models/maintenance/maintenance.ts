import { action, observable } from 'mobx';

import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import BaseStore from 'models/base_store';
import { makeRequest } from 'network';
import { RootStore } from 'state';

import { Maintenance, MaintenanceMode, MaintenanceType } from './maintenance.types';

export class MaintenanceStore extends BaseStore {
  @observable.shallow
  maintenances?: Maintenance[];

  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/maintenance/';
  }

  @action
  async updateMaintenances() {
    this.maintenances = await this.getAll();
  }

  @action
  async startMaintenanceMode(
    type: MaintenanceType,
    mode: MaintenanceMode,
    duration: number,
    alertReceiveChannelId?: AlertReceiveChannel['id']
  ) {
    return await makeRequest(`/start_maintenance/`, {
      method: 'POST',
      data: {
        type,
        mode,
        duration,
        alert_receive_channel_id: alertReceiveChannelId,
      },
      withCredentials: true,
    });
  }

  @action
  async stopMaintenanceMode(type: MaintenanceType, alertReceiveChannelId: AlertReceiveChannel['id']) {
    return await makeRequest(`/stop_maintenance/`, {
      method: 'POST',
      data: {
        type,
        alert_receive_channel_id: alertReceiveChannelId,
      },
      withCredentials: true,
    });
  }
}
