import { makeAutoObservable, runInAction } from 'mobx';
import { OnCallPluginMetaJSONData } from 'types';

import { ActionKey } from 'models/loader/action-keys';
import { GrafanaApiClient } from 'network/grafana-api/http-client';
import { makeRequest } from 'network/network';
import { PluginConnection, PostStatusResponse } from 'network/oncall-api/api.types';
import { RootBaseStore } from 'state/rootBaseStore/RootBaseStore';
import { AutoLoadingState } from 'utils/decorators';

import { PluginHelper } from './plugin.helper';

/* 
High-level OnCall initialization process:
On OSS:
  - On OnCall page / OnCall extension mount POST /status is called and it has pluginConfiguration object with different flags. 
    If all of them have `ok: true` , we consider plugin to be successfully configured and application loading is being continued. 
    Otherwise, we show error page with the option to go to plugin config (for Admin user) or to contact administrator (for nonAdmin user)
  - On plugin config page frontend sends another POST /status. If every flag has `ok: true`, it shows that plugin is connected. 
    Otherwise, it shows more detailed information of what is misconfigured / missing. User can update onCallApiUrl and try to reconnect plugin.
      - If Grafana version >= 10.3 AND externalServiceAccount feature flag is `true`, then grafana token is autoprovisioned and there is no need to create it
      - Otherwise, user is given the option to manually create service account as Admin and then reconnect the plugin
On Cloud:
  - On OnCall page / OnCall extension mount POST /status is called. If plugin is configured correctly, application loads as usual.
    If it's not, we show error page with the button to contact support
  - On plugin config page we show info if plugin is connected. If it's not we show detailed information of the errors and the button to contact support
*/

export class PluginStore {
  rootStore: RootBaseStore;
  connectionStatus?: PluginConnection;
  isPluginConnected = false;

  constructor(rootStore: RootBaseStore) {
    makeAutoObservable(this, undefined, { autoBind: true });
    this.rootStore = rootStore;
  }

  @AutoLoadingState(ActionKey.PLUGIN_VERIFY_CONNECTION)
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

  @AutoLoadingState(ActionKey.PLUGIN_UPDATE_SETTINGS_AND_REINITIALIZE)
  async updatePluginSettingsAndReinitializePlugin(jsonData: OnCallPluginMetaJSONData) {
    await GrafanaApiClient.updateGrafanaPluginSettings({ jsonData });
    await PluginHelper.install();
    await this.verifyPluginConnection();
  }

  @AutoLoadingState(ActionKey.PLUGIN_RECREATE_SERVICE_ACCOUNT)
  async recreateServiceAccountAndRecheckPluginStatus() {
    await GrafanaApiClient.recreateGrafanaTokenAndSaveInPluginSettings();
    await this.verifyPluginConnection();
  }
}
