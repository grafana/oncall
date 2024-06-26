import { makeObservable } from 'mobx';

import { BaseStore } from "models/base_store";
import { makeRequest } from 'network/network';
import { RootStore } from 'state/rootStore';

export class MattermostStore extends BaseStore {
  constructor(rootStore: RootStore) {
    super(rootStore);
    makeObservable(this);
  }

  async getMattermostSetupDetails() {
    return await makeRequest(`/mattermost/setup/`, {
      withCredentials: true
    })
  }
}
