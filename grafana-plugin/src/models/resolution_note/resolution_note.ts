import { action, makeObservable } from 'mobx';

import { Alert } from 'models/alertgroup/alertgroup.types';
import BaseStore from 'models/base_store';
import { makeRequest } from 'network';
import { RootStore } from 'state';

export class ResolutionNotesStore extends BaseStore {
  constructor(rootStore: RootStore) {
    super(rootStore);
    makeObservable(this);

    this.path = '/resolution_notes/';
  }

  @action.bound
  async createResolutionNote(alertGroupId: Alert['pk'], text: string) {
    return await makeRequest(`${this.path}`, {
      method: 'POST',
      data: { alert_group: alertGroupId, text: text },
    });
  }
}
