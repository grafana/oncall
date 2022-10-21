import { getBackendSrv } from '@grafana/runtime';

import { makeRequest } from 'network';

export const SYNC_STATUS_RETRY_LIMIT = 10;

export const createGrafanaToken = async () => {
  const keys = await getBackendSrv().get('/api/auth/keys');
  const existingKey = keys.find((key: { id: number; name: string; role: string }) => key.name === 'OnCall');

  if (existingKey) {
    await getBackendSrv().delete(`/api/auth/keys/${existingKey.id}`);
  }

  return getBackendSrv().post('/api/auth/keys', {
    name: 'OnCall',
    role: 'Admin',
    secondsToLive: null,
  });
};

export const updateGrafanaToken = (key: string) =>
  getBackendSrv().post(`/api/plugins/grafana-oncall-app/settings`, {
    enabled: true,
    pinned: true,
    secureJsonData: {
      grafanaToken: key,
    },
  });

export const startPluginSync = () => makeRequest('/plugin/sync', { method: 'POST' });

export const syncStatusDelay = (retryCount: number) =>
  new Promise((resolve) => setTimeout(resolve, 10 * 2 ** retryCount));

export const getPluginSyncStatus = () => makeRequest(`/plugin/sync`, { method: 'GET' });

export const installPlugin = async () => {
  const grafanaToken = await createGrafanaToken();
  await updateGrafanaToken(grafanaToken.key);
  return makeRequest('/plugin/install', { method: 'POST' });
};
