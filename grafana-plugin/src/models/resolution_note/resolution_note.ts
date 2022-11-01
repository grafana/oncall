import { observable } from 'mobx';

import { Alert } from 'models/alertgroup/alertgroup.types';
import BaseStore from 'models/base_store';
import { makeRequest } from 'network';
import { RootStore } from 'state';

import { ResolutionNote } from './resolution_note.types';

export class ResolutionNotesStore extends BaseStore {
  @observable.shallow
  resolutionNotes: { [id: string]: ResolutionNote[] } = {};

  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/resolution_notes/';
  }

  async createResolutionNote(alertGroupId: Alert['pk'], text: string) {
    return await makeRequest(`${this.path}`, {
      method: 'POST',
      data: { alert_group: alertGroupId, text: text },
    });
  }
}
