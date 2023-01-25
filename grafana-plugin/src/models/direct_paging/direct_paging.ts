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
}
