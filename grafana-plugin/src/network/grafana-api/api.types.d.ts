import { OnCallPluginMetaJSONData, OnCallPluginMetaSecureJSONData } from 'app-types';

export type ServiceAccountDTO = {
  description: string;
  accessControl: { [key: string]: boolean };
  avatarUrl: string;
  id: number;
  isDisabled: boolean;
  login: string;
  name: string;
  orgId: number;
  role: string;
  tokens: number;
};

export type PaginatedServiceAccounts = {
  page: number;
  perPage: number;
  serviceAccounts: ServiceAccountDTO[];
  totalCount: number;
};

export type TokenDTO = {
  created: string;
  expiration: string;
  hasExpired: boolean;
  id: number;
  isRevoked: boolean;
  lastUsedAt: string;
  name: string;
  secondsUntilExpiration: number;
};

export type ApiAuthKeyDTO = {
  accessControl: { [key: string]: boolean };
  expiration: string;
  id: number;
  lastUsedAt: string;
  name: string;
  role: 'None' | 'Viewer' | 'Editor' | 'Admin';
};

export type NewApiKeyResult = {
  id: number;
  key: string;
  name: string;
};

export type UpdateGrafanaPluginSettingsProps = {
  jsonData?: Partial<OnCallPluginMetaJSONData>;
  secureJsonData?: Partial<OnCallPluginMetaSecureJSONData>;
};
