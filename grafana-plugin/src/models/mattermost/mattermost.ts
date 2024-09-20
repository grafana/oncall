import { GENERIC_ERROR } from 'helpers/consts';
import { openErrorNotification } from 'helpers/helpers';
import { makeObservable } from 'mobx';

import { BaseStore } from 'models/base_store';
import { makeRequestRaw } from 'network/network';
import { RootStore } from 'state/rootStore';

export class MattermostStore extends BaseStore {
  constructor(rootStore: RootStore) {
    super(rootStore);
    makeObservable(this);
  }

  async mattermostLogin() {
    try {
      const response = await makeRequestRaw('/login/mattermost-login/', {});

      if (response.status === 201) {
        this.rootStore.organizationStore.loadCurrentOrganization();
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
