import { getBackendSrv } from '@grafana/runtime';
import { OnCallAppPluginMeta, OnCallPluginMetaJSONData, OnCallPluginMetaSecureJSONData } from 'types';

import { makeRequest, isNetworkError } from 'network';

export type UpdateGrafanaPluginSettingsProps = {
  jsonData?: Partial<OnCallPluginMetaJSONData>;
  secureJsonData?: Partial<OnCallPluginMetaSecureJSONData>;
};

export type PluginStatusResponseBase = Pick<OnCallPluginMetaJSONData, 'license'> & {
  version: string;
  recaptcha_site_key: string;
  currently_undergoing_maintenance_message: string;
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
  static grafanaBackend = getBackendSrv();

  static generateOnCallApiUrlConfiguredThroughEnvVarMsg = (isConfiguredThroughEnvVar: boolean): string =>
    isConfiguredThroughEnvVar ? ' (NOTE: OnCall API URL is currently being taken from process.env of your UI)' : '';

  static generateInvalidOnCallApiURLErrorMsg = (onCallApiUrl: string, isConfiguredThroughEnvVar: boolean): string =>
    `Could not communicate with OnCall API at ${onCallApiUrl}${this.generateOnCallApiUrlConfiguredThroughEnvVarMsg(
      isConfiguredThroughEnvVar
    )}.\nValidate that the URL is correct, OnCall API is running, and that it is accessible from your Grafana instance.`;

  static generateUnknownErrorMsg = (
    onCallApiUrl: string,
    verb: InstallationVerb,
    isConfiguredThroughEnvVar: boolean
  ): string =>
    `An unknown error occurred when trying to ${verb} the plugin. Verify OnCall API URL, ${onCallApiUrl}, is correct${this.generateOnCallApiUrlConfiguredThroughEnvVarMsg(
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
    const consoleMsg = `occurred while trying to ${installationVerb} the plugin w/ the OnCall backend`;

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
      // a non-network related error occurred.. this scenario shouldn't occur...
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
      console.warn('An HTTP related error occurred while trying to provision the plugin w/ Grafana', e.response);
      errorMsg = this.generateInvalidOnCallApiURLErrorMsg(onCallApiUrl, onCallApiUrlIsConfiguredThroughEnvVar);
    } else {
      // a non-network related error occurred.. this scenario shouldn't occur...
      console.warn('An unknown error occurred while trying to provision the plugin w/ Grafana', e);
      errorMsg = this.generateUnknownErrorMsg(onCallApiUrl, installationVerb, onCallApiUrlIsConfiguredThroughEnvVar);
    }
    return errorMsg;
  };

  static getGrafanaPluginSettings = async (): Promise<OnCallAppPluginMeta> =>
    this.grafanaBackend.get<OnCallAppPluginMeta>(this.GRAFANA_PLUGIN_SETTINGS_URL);

  static updateGrafanaPluginSettings = async (data: UpdateGrafanaPluginSettingsProps, enabled = true) =>
    this.grafanaBackend.post(this.GRAFANA_PLUGIN_SETTINGS_URL, { ...data, enabled, pinned: true });

  static readonly KEYS_BASE_URL = '/api/auth/keys';
  static readonly ONCALL_KEY_NAME = 'OnCall';
  static readonly SERVICE_ACCOUNTS_BASE_URL = '/api/serviceaccounts';
  static readonly ONCALL_SERVICE_ACCOUNT_NAME = 'sa-autogen-OnCall';
  static readonly SERVICE_ACCOUNTS_SEARCH_URL = `${PluginState.SERVICE_ACCOUNTS_BASE_URL}/search?query=${PluginState.ONCALL_SERVICE_ACCOUNT_NAME}`;

  static getServiceAccount = async () => {
    const serviceAccounts = await this.grafanaBackend.get(this.SERVICE_ACCOUNTS_SEARCH_URL);
    return serviceAccounts.serviceAccounts.length > 0 ? serviceAccounts.serviceAccounts[0] : null;
  };

  static getOrCreateServiceAccount = async () => {
    const serviceAccount = await this.getServiceAccount();
    if (serviceAccount) {
      return serviceAccount;
    }

    return await this.grafanaBackend.post(this.SERVICE_ACCOUNTS_BASE_URL, {
      name: this.ONCALL_SERVICE_ACCOUNT_NAME,
      role: 'Admin',
      isDisabled: false,
    });
  };

  static getTokenFromServiceAccount = async (serviceAccount) => {
    const tokens = await this.grafanaBackend.get(`${this.SERVICE_ACCOUNTS_BASE_URL}/${serviceAccount.id}/tokens`);
    return tokens.find((key: { id: number; name: string; role: string }) => key.name === PluginState.ONCALL_KEY_NAME);
  };

  /**
   * This will satisfy a check for an existing key regardless of if the key is an older api key or under a
   * service account.
   */
  static getGrafanaToken = async () => {
    const serviceAccount = await this.getServiceAccount();
    if (serviceAccount) {
      return await this.getTokenFromServiceAccount(serviceAccount);
    }

    const keys = await this.grafanaBackend.get(this.KEYS_BASE_URL);
    const oncallApiKeys = keys.find(
      (key: { id: number; name: string; role: string }) => key.name === PluginState.ONCALL_KEY_NAME
    );
    if (oncallApiKeys) {
      return oncallApiKeys;
    }

    return null;
  };

  /**
   * Create service account and api token belonging to it instead of using api keys
   */
  static createGrafanaToken = async () => {
    const serviceAccount = await this.getOrCreateServiceAccount();
    const existingToken = await this.getTokenFromServiceAccount(serviceAccount);
    if (existingToken) {
      await this.grafanaBackend.delete(
        `${this.SERVICE_ACCOUNTS_BASE_URL}/${serviceAccount.id}/tokens/${existingToken.id}`
      );
    }

    const existingKey = await this.getGrafanaToken();
    if (existingKey) {
      await this.grafanaBackend.delete(`${this.KEYS_BASE_URL}/${existingKey.id}`);
    }

    return await this.grafanaBackend.post(`${this.SERVICE_ACCOUNTS_BASE_URL}/${serviceAccount.id}/tokens`, {
      name: PluginState.ONCALL_KEY_NAME,
      role: 'Admin',
    });
  };

  static checkTokenAndIfPluginIsConnected = async (
    onCallApiUrl: string
  ): Promise<PluginSyncStatusResponse | string> => {
    /**
     * Allows the plugin config page to repair settings like the app initialization screen if a user deletes
     * an API key on accident but leaves the plugin settings intact.
     */
    const existingKey = await PluginState.getGrafanaToken();
    if (!existingKey) {
      try {
        await PluginState.installPlugin();
      } catch (e) {
        return PluginState.getHumanReadableErrorFromOnCallError(e, onCallApiUrl, 'install', false);
      }
    }

    return await PluginState.updatePluginStatus(onCallApiUrl);
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

  static updatePluginStatus = async (
    onCallApiUrl: string,
    onCallApiUrlIsConfiguredThroughEnvVar = false
  ): Promise<PluginConnectedStatusResponse | string> => {
    try {
      return await makeRequest<PluginConnectedStatusResponse>(`${this.ONCALL_BASE_URL}/status`, {
        method: 'POST',
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
