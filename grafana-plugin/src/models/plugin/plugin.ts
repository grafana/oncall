import { OnCallPluginMetaJSONData } from 'app-types';
import { waitInMs } from 'helpers/async';
import { AutoLoadingState } from 'helpers/decorators';
import { isEqual } from 'lodash-es';
import { makeAutoObservable, runInAction } from 'mobx';

import { ActionKey } from 'models/loader/action-keys';
import { GrafanaApiClient } from 'network/grafana-api/http-client';
import { makeRequest } from 'network/network';
import { PluginConnection, StatusResponse } from 'network/oncall-api/api.types';
import { RootBaseStore } from 'state/rootBaseStore/RootBaseStore';

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
  apiUrlFromStatus?: string;
  isPluginConnected = false;
  appliedOnCallApiUrl = '';

  constructor(rootStore: RootBaseStore) {
    makeAutoObservable(this, undefined, { autoBind: true });
    this.rootStore = rootStore;
  }

  private resetConnectionStatus() {
    this.connectionStatus = undefined;
    this.isPluginConnected = false;
  }

  async refreshAppliedOnCallApiUrl() {
    const { jsonData } = await GrafanaApiClient.getGrafanaPluginSettings();
    runInAction(() => {
      this.appliedOnCallApiUrl = jsonData.onCallApiUrl;
    });
  }

  @AutoLoadingState(ActionKey.PLUGIN_VERIFY_CONNECTION)
  async verifyPluginConnection() {
    const { pluginConnection, api_url } = await makeRequest<StatusResponse>(`/plugin/status`, {});
    runInAction(() => {
      this.connectionStatus = pluginConnection;
      this.apiUrlFromStatus = api_url;
      this.isPluginConnected = Object.keys(pluginConnection).every(
        (key) => pluginConnection[key as keyof PluginConnection]?.ok
      );
    });
  }

  @AutoLoadingState(ActionKey.PLUGIN_UPDATE_SETTINGS_AND_REINITIALIZE)
  async updatePluginSettingsAndReinitializePlugin({
    currentJsonData,
    newJsonData,
  }: {
    currentJsonData: OnCallPluginMetaJSONData;
    newJsonData: Partial<OnCallPluginMetaJSONData>;
  }) {
    this.resetConnectionStatus();
    const saveJsonDataCandidate = { ...currentJsonData, ...newJsonData };
    if (!isEqual(currentJsonData, saveJsonDataCandidate) || !this.connectionStatus?.oncall_api_url?.ok) {
      await GrafanaApiClient.updateGrafanaPluginSettings({ jsonData: saveJsonDataCandidate });
      await waitInMs(1000); // It's required for backend proxy to pick up new settings
    }
    try {
      await PluginHelper.install();
    } finally {
      await this.verifyPluginConnection();
    }
  }

  @AutoLoadingState(ActionKey.PLUGIN_RECREATE_SERVICE_ACCOUNT)
  async recreateServiceAccountAndRecheckPluginStatus() {
    await GrafanaApiClient.recreateGrafanaTokenAndSaveInPluginSettings();
    await this.verifyPluginConnection();
  }

  async enablePlugin() {
    await GrafanaApiClient.updateGrafanaPluginSettings({}, true);
    location.reload();
  }
}
