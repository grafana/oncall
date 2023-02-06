import { Alert } from 'models/alertgroup/alertgroup.types';
import BaseStore from 'models/base_store';
import { makeRequest } from 'network';
import { RootStore } from 'state';

export class DirectPagingStore extends BaseStore {
  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/direct_paging/';
  }

  async createManualAlertRule(data: any) {
    return await makeRequest(`${this.path}`, {
      method: 'POST',
      data,
    });
  }

  async updateAlertGroup(alertId: Alert['pk'], data: any) {
    return await makeRequest(`${this.path}`, {
      method: 'POST',
      data: {
        alert_group_id: alertId,
        ...data,
      },
    });
  }
}
