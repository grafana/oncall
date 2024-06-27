import { getBackendSrv } from '@grafana/runtime';
import { OnCallPluginMetaJSONData } from 'types';

import {
  ApiAuthKeyDTO,
  NewApiKeyResult,
  PaginatedServiceAccounts,
  ServiceAccountDTO,
  TokenDTO,
  UpdateGrafanaPluginSettingsProps,
} from './api.types';

const KEYS_BASE_URL = '/api/auth/keys';
const SERVICE_ACCOUNTS_BASE_URL = '/api/serviceaccounts';
const ONCALL_KEY_NAME = 'OnCall';
const ONCALL_SERVICE_ACCOUNT_NAME = 'sa-autogen-OnCall';
const GRAFANA_PLUGIN_SETTINGS_URL = '/api/plugins/grafana-oncall-app/settings';

export class GrafanaApiClient {
  static grafanaBackend = getBackendSrv();

  private static getServiceAccount = async () => {
    const serviceAccounts = await this.grafanaBackend.get<PaginatedServiceAccounts>(
      `${SERVICE_ACCOUNTS_BASE_URL}/search?query=${ONCALL_SERVICE_ACCOUNT_NAME}`
    );
    return serviceAccounts.serviceAccounts.length > 0 ? serviceAccounts.serviceAccounts[0] : null;
  };

  private static getOrCreateServiceAccount = async () => {
    const serviceAccount = await this.getServiceAccount();
    if (serviceAccount) {
      return serviceAccount;
    }

    return await this.grafanaBackend.post<ServiceAccountDTO>(SERVICE_ACCOUNTS_BASE_URL, {
      name: ONCALL_SERVICE_ACCOUNT_NAME,
      role: 'Admin',
      isDisabled: false,
    });
  };

  private static getTokenFromServiceAccount = async (serviceAccount) => {
    const tokens = await this.grafanaBackend.get<TokenDTO[]>(
      `${SERVICE_ACCOUNTS_BASE_URL}/${serviceAccount.id}/tokens`
    );
    return tokens.find(({ name }) => name === ONCALL_KEY_NAME);
  };

  private static getGrafanaToken = async () => {
    const serviceAccount = await this.getServiceAccount();
    if (serviceAccount) {
      return await this.getTokenFromServiceAccount(serviceAccount);
    }

    const keys = await this.grafanaBackend.get<ApiAuthKeyDTO[]>(KEYS_BASE_URL);
    return keys.find(({ name }) => name === ONCALL_KEY_NAME);
  };

  static updateGrafanaPluginSettings = async (data: UpdateGrafanaPluginSettingsProps, enabled = true) =>
    this.grafanaBackend.post(GRAFANA_PLUGIN_SETTINGS_URL, { ...data, enabled, pinned: true });

  static getGrafanaPluginSettings = async () =>
    this.grafanaBackend.get<{ jsonData: OnCallPluginMetaJSONData }>(GRAFANA_PLUGIN_SETTINGS_URL);

  static recreateGrafanaTokenAndSaveInPluginSettings = async () => {
    const serviceAccount = await this.getOrCreateServiceAccount();

    const existingToken = await this.getTokenFromServiceAccount(serviceAccount);
    if (existingToken) {
      await this.grafanaBackend.delete(`${SERVICE_ACCOUNTS_BASE_URL}/${serviceAccount.id}/tokens/${existingToken.id}`);
    }

    const existingKey = await this.getGrafanaToken();
    if (existingKey) {
      await this.grafanaBackend.delete(`${KEYS_BASE_URL}/${existingKey.id}`);
    }

    const { key: grafanaToken } = await this.grafanaBackend.post<NewApiKeyResult>(
      `${SERVICE_ACCOUNTS_BASE_URL}/${serviceAccount.id}/tokens`,
      {
        name: ONCALL_KEY_NAME,
        role: 'Admin',
      }
    );

    await this.updateGrafanaPluginSettings({ secureJsonData: { grafanaToken } });
  };
}
