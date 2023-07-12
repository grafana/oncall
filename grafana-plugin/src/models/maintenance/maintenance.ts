import { action, observable } from 'mobx';

import BaseStore from 'models/base_store';
import { RootStore } from 'state';

import { Maintenance } from './maintenance.types';

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
}
