import { getBackendSrv } from '@grafana/runtime';
import { OnCallAppPluginMeta, OnCallPluginMetaJSONData, OnCallPluginMetaSecureJSONData } from 'types';

import { makeRequest, isNetworkError } from 'network';
import FaroHelper from 'utils/faro';

export type UpdateGrafanaPluginSettingsProps = {
  jsonData?: Partial<OnCallPluginMetaJSONData>;
  secureJsonData?: Partial<OnCallPluginMetaSecureJSONData>;
};

export type PluginStatusResponseBase = Pick<OnCallPluginMetaJSONData, 'license'> & {
  version: string;
};

export type PluginSyncStatusResponse = PluginStatusResponseBase & {
  token_ok: boolean;
  recaptcha_site_key: string;
};

type PluginConnectedStatusResponse = PluginStatusResponseBase & {
  is_installed: boolean;
  token_ok: boolean;
  allow_signup: boolean;
  is_user_anonymous: boolean;
};

type PluginIsInMaintenanceModeResponse = {
  currently_undergoing_maintenance_message: string;
};

type CloudProvisioningConfigResponse = null;

type SelfHostedProvisioningConfigResponse = Omit<OnCallPluginMetaJSONData, 'onCallApiUrl'> & {
  onCallToken: string;
};

type InstallPluginResponse<OnCallAPIResponse = any> = Pick<OnCallPluginMetaSecureJSONData, 'grafanaToken'> & {
  onCallAPIResponse: OnCallAPIResponse;
};

export type InstallationVerb = 'install' | 'sync';

class PluginState {
  static ONCALL_BASE_URL = '/plugin';
  static GRAFANA_PLUGIN_SETTINGS_URL = '/api/plugins/grafana-oncall-app/settings';
  static SYNC_STATUS_POLLING_RETRY_LIMIT = 10;
  static grafanaBackend = getBackendSrv();

  static generateOnCallApiUrlConfiguredThroughEnvVarMsg = (isConfiguredThroughEnvVar: boolean): string =>
    isConfiguredThroughEnvVar
      ? ' (NOTE: your OnCall API URL is currently being taken from process.env of your UI)'
      : '';

  static generateInvalidOnCallApiURLErrorMsg = (onCallApiUrl: string, isConfiguredThroughEnvVar: boolean): string =>
    `Could not communicate with your OnCall API at ${onCallApiUrl}${this.generateOnCallApiUrlConfiguredThroughEnvVarMsg(
      isConfiguredThroughEnvVar
    )}.\nValidate that the URL is correct, your OnCall API is running, and that it is accessible from your Grafana instance.`;

  static generateUnknownErrorMsg = (
    onCallApiUrl: string,
    verb: InstallationVerb,
    isConfiguredThroughEnvVar: boolean
  ): string =>
    `An unknown error occured when trying to ${verb} the plugin. Are you sure that your OnCall API URL, ${onCallApiUrl}, is correct${this.generateOnCallApiUrlConfiguredThroughEnvVarMsg(
      isConfiguredThroughEnvVar
    )}?\nRefresh your page and try again, or try removing your plugin configuration and reconfiguring.`;

  static getHumanReadableErrorFromOnCallError = (
    e: any,
    onCallApiUrl: string,
    installationVerb: InstallationVerb,
    onCallApiUrlIsConfiguredThroughEnvVar = false
  ): string => {
    let errorMsg: string;
    const unknownErrorMsg = this.generateUnknownErrorMsg(
      onCallApiUrl,
      installationVerb,
      onCallApiUrlIsConfiguredThroughEnvVar
    );
    const consoleMsg = `occured while trying to ${installationVerb} the plugin w/ the OnCall backend`;

    if (isNetworkError(e)) {
      const { status: statusCode } = e.response;

      console.warn(`An HTTP related error ${consoleMsg}`, e.response);

      if (statusCode === 502) {
        // 502 occurs when the plugin-proxy cannot communicate w/ the OnCall API using the provided URL
        errorMsg = this.generateInvalidOnCallApiURLErrorMsg(onCallApiUrl, onCallApiUrlIsConfiguredThroughEnvVar);
      } else if (statusCode === 400) {
        /**
         * A 400 is 'bubbled-up' from the OnCall API. It indicates one of three cases:
         * 1. there is a communication error when OnCall API tries to contact Grafana's API
         * 2. there is an auth error when OnCall API tries to contact Grafana's API
         * 3. (likely rare) user inputs an onCallApiUrl that is not RFC 1034/1035 compliant
         *
         * Check if the response body has an 'error' JSON attribute, if it does, assume scenario 1 or 2
         * Use the error message provided to give the user more context/helpful debugging information
         */
        errorMsg = e.response.data?.error || unknownErrorMsg;
      } else {
        // this scenario shouldn't occur..
        errorMsg = unknownErrorMsg;
      }
    } else {
      // a non-network related error occured.. this scenario shouldn't occur...
      console.warn(`An unknown error ${consoleMsg}`, e);
      errorMsg = unknownErrorMsg;
    }
    return errorMsg;
  };

  static getHumanReadableErrorFromGrafanaProvisioningError = (
    e: any,
    onCallApiUrl: string,
    installationVerb: InstallationVerb,
    onCallApiUrlIsConfiguredThroughEnvVar: boolean
  ): string => {
    let errorMsg: string;

    if (isNetworkError(e)) {
      // The user likely put in a bogus URL for the OnCall API URL
      console.warn('An HTTP related error occured while trying to provision the plugin w/ Grafana', e.response);
      errorMsg = this.generateInvalidOnCallApiURLErrorMsg(onCallApiUrl, onCallApiUrlIsConfiguredThroughEnvVar);
    } else {
      // a non-network related error occured.. this scenario shouldn't occur...
      console.warn('An unknown error occured while trying to provision the plugin w/ Grafana', e);
      errorMsg = this.generateUnknownErrorMsg(onCallApiUrl, installationVerb, onCallApiUrlIsConfiguredThroughEnvVar);
    }
    return errorMsg;
  };

  static getGrafanaPluginSettings = async (): Promise<OnCallAppPluginMeta> =>
    this.grafanaBackend.get<OnCallAppPluginMeta>(this.GRAFANA_PLUGIN_SETTINGS_URL);

  static updateGrafanaPluginSettings = async (data: UpdateGrafanaPluginSettingsProps, enabled = true) =>
    this.grafanaBackend.post(this.GRAFANA_PLUGIN_SETTINGS_URL, { ...data, enabled, pinned: true });

  static readonly KEYS_BASE_URL = '/api/auth/keys';

  static getGrafanaToken = async () => {
    const keys = await this.grafanaBackend.get(this.KEYS_BASE_URL);
    return keys.find((key: { id: number; name: string; role: string }) => key.name === 'OnCall');
  };

  static createGrafanaToken = async () => {
    const existingKey = await this.getGrafanaToken();
    if (existingKey) {
      await this.grafanaBackend.delete(`${this.KEYS_BASE_URL}/${existingKey.id}`);
    }

    return await this.grafanaBackend.post(this.KEYS_BASE_URL, {
      name: 'OnCall',
      role: 'Admin',
      secondsToLive: null,
    });
  };

  static getPluginSyncStatus = (): Promise<PluginSyncStatusResponse> =>
    makeRequest<PluginSyncStatusResponse>(`${this.ONCALL_BASE_URL}/sync`, { method: 'GET' });

  static timeout = (pollCount: number) => new Promise((resolve) => setTimeout(resolve, 10 * 2 ** pollCount));

  /**
   * DON'T CALL THIS METHOD DIRECTLY
   * This really only exists to properly test the recursive nature of pollOnCallDataSyncStatus
   * Without this it is impossible (or very hacky) to mock the recursive calls
   */
  static _pollOnCallDataSyncStatus = (
    onCallApiUrl: string,
    onCallApiUrlIsConfiguredThroughEnvVar: boolean,
    pollCount: number
  ) => this.pollOnCallDataSyncStatus(onCallApiUrl, onCallApiUrlIsConfiguredThroughEnvVar, pollCount);

  /**
   * Poll, for a configured amount of time, the status of the OnCall backend data sync
   * Returns a PluginSyncStatusResponse if the sync was successful (ie. token_ok is true), otherwise null
   */
  static pollOnCallDataSyncStatus = async (
    onCallApiUrl: string,
    onCallApiUrlIsConfiguredThroughEnvVar: boolean,
    pollCount = 0
  ): Promise<PluginSyncStatusResponse | string> => {
    if (pollCount > this.SYNC_STATUS_POLLING_RETRY_LIMIT) {
      return `There was an issue while synchronizing data required for the plugin.\nVerify your OnCall backend setup (ie. that Celery workers are launched and properly configured)`;
    }

    try {
      const syncResponse = await this.getPluginSyncStatus();
      if (syncResponse?.token_ok) {
        return syncResponse;
      }

      await this.timeout(pollCount);
      return await this._pollOnCallDataSyncStatus(onCallApiUrl, onCallApiUrlIsConfiguredThroughEnvVar, pollCount + 1);
    } catch (e) {
      return this.getHumanReadableErrorFromOnCallError(e, onCallApiUrl, 'sync', onCallApiUrlIsConfiguredThroughEnvVar);
    }
  };

  /**
   * Trigger a data sync with the OnCall backend AND then poll, for a configured amount of time, the status of that sync
   * If the
   * Returns a PluginSyncStatusResponse if the sync was succesful, otherwise null
   */
  static syncDataWithOnCall = async (
    onCallApiUrl: string,
    onCallApiUrlIsConfiguredThroughEnvVar = false
  ): Promise<PluginSyncStatusResponse | string> => {
    try {
      /**
       * Allows the plugin config page to repair settings like the app initialization screen if a user deletes
       * an API on accident but leaves the plugin settings intact.
       */
      const existingKey = await this.getGrafanaToken();
      if (!existingKey) {
        await this.installPlugin();
      }

      const startSyncResponse = await makeRequest(`${this.ONCALL_BASE_URL}/sync`, { method: 'POST' });
      if (typeof startSyncResponse === 'string') {
        // an error occured trying to initiate the sync
        return startSyncResponse;
      }

      if (!FaroHelper.faro) {
        FaroHelper.initializeFaro(onCallApiUrl);
      }

      return await this.pollOnCallDataSyncStatus(onCallApiUrl, onCallApiUrlIsConfiguredThroughEnvVar);
    } catch (e) {
      return this.getHumanReadableErrorFromOnCallError(e, onCallApiUrl, 'sync', onCallApiUrlIsConfiguredThroughEnvVar);
    }
  };

  static installPlugin = async <RT = CloudProvisioningConfigResponse>(
    selfHosted = false
  ): Promise<InstallPluginResponse<RT>> => {
    const { key: grafanaToken } = await this.createGrafanaToken();
    await this.updateGrafanaPluginSettings({ secureJsonData: { grafanaToken } });
    const onCallAPIResponse = await makeRequest<RT>(
      `${this.ONCALL_BASE_URL}/${selfHosted ? 'self-hosted/' : ''}install`,
      {
        method: 'POST',
      }
    );
    return { grafanaToken, onCallAPIResponse };
  };

  static selfHostedInstallPlugin = async (
    onCallApiUrl: string,
    onCallApiUrlIsConfiguredThroughEnvVar: boolean
  ): Promise<string | null> => {
    let pluginInstallationOnCallResponse: InstallPluginResponse<SelfHostedProvisioningConfigResponse>;
    const errorMsgVerb: InstallationVerb = 'install';

    // Step 1. Try provisioning the plugin w/ the Grafana API
    try {
      await this.updateGrafanaPluginSettings({ jsonData: { onCallApiUrl: onCallApiUrl } });
    } catch (e) {
      return this.getHumanReadableErrorFromGrafanaProvisioningError(
        e,
        onCallApiUrl,
        errorMsgVerb,
        onCallApiUrlIsConfiguredThroughEnvVar
      );
    }

    /**
     * Step 2:
     * - Create a grafana token
     * - store that token in the Grafana plugin settings
     * - configure the plugin in OnCall's backend
     */
    try {
      pluginInstallationOnCallResponse = await this.installPlugin<SelfHostedProvisioningConfigResponse>(true);
    } catch (e) {
      return this.getHumanReadableErrorFromOnCallError(
        e,
        onCallApiUrl,
        errorMsgVerb,
        onCallApiUrlIsConfiguredThroughEnvVar
      );
    }

    // Step 3. reprovision the Grafana plugin settings, storing information that we get back from OnCall's backend
    try {
      const {
        grafanaToken,
        onCallAPIResponse: { onCallToken: onCallApiToken, ...jsonData },
      } = pluginInstallationOnCallResponse;

      await this.updateGrafanaPluginSettings({
        jsonData: {
          ...jsonData,
          onCallApiUrl,
        },
        secureJsonData: {
          grafanaToken,
          onCallApiToken,
        },
      });
    } catch (e) {
      return this.getHumanReadableErrorFromGrafanaProvisioningError(
        e,
        onCallApiUrl,
        errorMsgVerb,
        onCallApiUrlIsConfiguredThroughEnvVar
      );
    }

    return null;
  };

  static checkIfBackendIsInMaintenanceMode = async (
    onCallApiUrl: string,
    onCallApiUrlIsConfiguredThroughEnvVar = false
  ): Promise<PluginIsInMaintenanceModeResponse | string> => {
    try {
      return await makeRequest<PluginIsInMaintenanceModeResponse>('/maintenance-mode-status', {
        method: 'GET',
      });
    } catch (e) {
      return this.getHumanReadableErrorFromOnCallError(
        e,
        onCallApiUrl,
        'install',
        onCallApiUrlIsConfiguredThroughEnvVar
      );
    }
  };

  static checkIfPluginIsConnected = async (
    onCallApiUrl: string,
    onCallApiUrlIsConfiguredThroughEnvVar = false
  ): Promise<PluginConnectedStatusResponse | string> => {
    try {
      return await makeRequest<PluginConnectedStatusResponse>(`${this.ONCALL_BASE_URL}/status`, {
        method: 'GET',
      });
    } catch (e) {
      return this.getHumanReadableErrorFromOnCallError(
        e,
        onCallApiUrl,
        'install',
        onCallApiUrlIsConfiguredThroughEnvVar
      );
    }
  };

  static resetPlugin = (): Promise<void> => {
    /**
     * mark both of these objects as Required.. this will ensure that we are resetting every attribute back to null
     * and throw a type error in the event that OnCallPluginMetaJSONData or OnCallPluginMetaSecureJSONData is updated
     * but we forget to add the attribute here
     */
    const jsonData: Required<OnCallPluginMetaJSONData> = {
      stackId: null,
      orgId: null,
      onCallApiUrl: null,
      license: null,
    };
    const secureJsonData: Required<OnCallPluginMetaSecureJSONData> = {
      grafanaToken: null,
      onCallApiToken: null,
    };

    return this.updateGrafanaPluginSettings({ jsonData, secureJsonData }, false);
  };
}

export default PluginState;
