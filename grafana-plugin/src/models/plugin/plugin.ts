import { makeAutoObservable, runInAction } from 'mobx';

import { ActionKey } from 'models/loader/action-keys';
import { makeRequest } from 'network/network';
import { PluginConnection, PostStatusResponse } from 'network/oncall-api/api.types';
import { RootBaseStore } from 'state/rootBaseStore/RootBaseStore';
import { AutoLoadingState } from 'utils/decorators';
import { getIsRunningOpenSourceVersion } from 'utils/utils';

export class PluginStore {
  rootStore: RootBaseStore;
  connectionStatus?: PluginConnection;
  isPluginConnected = false;

  constructor(rootStore: RootBaseStore) {
    makeAutoObservable(this, undefined, { autoBind: true });
    this.rootStore = rootStore;
  }

  async verifyPluginConnection() {
    const { pluginConnection } = await makeRequest<PostStatusResponse>(`/plugin/status`, {
      method: 'POST',
    });
    runInAction(() => {
      this.connectionStatus = pluginConnection;
      this.isPluginConnected = Object.keys(pluginConnection).every(
        (key) => pluginConnection[key as keyof PluginConnection]?.ok
      );
    });
  }

  @AutoLoadingState(ActionKey.INITIALIZE_PLUGIN)
  async initializePlugin() {
    // create oncall api token and save in plugin settings
    const install = async () => {
      await makeRequest(`/plugin${getIsRunningOpenSourceVersion() ? '/self-hosted' : ''}/install`, {
        method: 'POST',
      });
    };

    // 1. Check if plugin is connected
    await this.verifyPluginConnection();
    if (!this.isPluginConnected) {
      // 2. if not connected try to install
      await install();
      // 3. Check if plugin is connected once again after install
      await this.verifyPluginConnection();
    }
  }
}
