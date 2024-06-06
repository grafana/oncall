import { makeAutoObservable } from 'mobx';

import { ActionKey } from 'models/loader/action-keys';
import { makeRequest } from 'network/network';
import { RootBaseStore } from 'state/rootBaseStore/RootBaseStore';
import { AutoLoadingState } from 'utils/decorators';
import { getIsRunningOpenSourceVersion } from 'utils/utils';

export class PluginStore {
  rootStore: RootBaseStore;
  isPluginInitialized = false;

  constructor(rootStore: RootBaseStore) {
    makeAutoObservable(this, undefined, { autoBind: true });
    this.rootStore = rootStore;
  }

  setIsPluginInitialized(value: boolean) {
    this.isPluginInitialized = value;
  }

  @AutoLoadingState(ActionKey.INITIALIZE_PLUGIN)
  async initializePlugin() {
    const IS_OPEN_SOURCE = getIsRunningOpenSourceVersion();

    // create oncall api token and save in plugin settings
    const install = async () => {
      await makeRequest(`/plugin${IS_OPEN_SOURCE ? '/self-hosted' : ''}/install`, {
        method: 'POST',
      });
    };

    // trigger users sync
    try {
      // TODO: once we improve backend we should get rid of token_ok check and call install() only in catch block
      const { token_ok } = await makeRequest(`/plugin/status`, {
        method: 'POST',
      });
      if (!token_ok) {
        await install();
      }
    } catch (_err) {
      await install();
    }

    this.setIsPluginInitialized(true);
  }
}
