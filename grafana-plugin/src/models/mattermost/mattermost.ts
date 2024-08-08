import { makeObservable } from 'mobx';

import { BaseStore } from 'models/base_store';
import { makeRequestRaw } from 'network/network';
import { RootStore } from 'state/rootStore';
import { GENERIC_ERROR } from 'utils/consts';
import { openErrorNotification } from 'utils/utils';

export class MattermostStore extends BaseStore {
  constructor(rootStore: RootStore) {
    super(rootStore);
    makeObservable(this);
  }

  async installMattermostIntegration() {
    try {
      const response = await makeRequestRaw('/login/mattermost-install/', {});

      if (response.status === 201) {
        this.rootStore.organizationStore.loadCurrentOrganizationConfigChecks();
      } else if (response.status === 200) {
        window.location = response.data;
      }
    } catch (ex) {
      if (ex.response?.status === 500) {
        openErrorNotification(GENERIC_ERROR);
      }
    }
  }
}
