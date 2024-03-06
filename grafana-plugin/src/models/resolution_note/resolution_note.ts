import { BaseStore } from 'models/base_store';
import { makeRequest } from 'network/network';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { RootStore } from 'state/rootStore';

export class ResolutionNotesStore extends BaseStore {
  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/resolution_notes/';
  }

  async createResolutionNote(alertGroupId: ApiSchemas['AlertGroup']['pk'], text: string) {
    return await makeRequest(`${this.path}`, {
      method: 'POST',
      data: { alert_group: alertGroupId, text: text },
    });
  }
}
