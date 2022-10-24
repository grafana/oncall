import { getBackendSrv } from '@grafana/runtime';

import { makeRequest } from 'network';

export async function createGrafanaToken() {
  const keys = await getBackendSrv().get('/api/auth/keys');
  const existingKey = keys.find((key: { id: number; name: string; role: string }) => key.name === 'OnCall');

  if (existingKey) {
    await getBackendSrv().delete(`/api/auth/keys/${existingKey.id}`);
  }

  return await getBackendSrv().post('/api/auth/keys', {
    name: 'OnCall',
    role: 'Admin',
    secondsToLive: null,
  });
}

export async function updateGrafanaToken(key: string) {
  await getBackendSrv().post(`/api/plugins/grafana-oncall-app/settings`, {
    enabled: true,
    pinned: true,
    secureJsonData: {
      grafanaToken: key,
    },
  });
}

export async function startPluginSync() {
  return await makeRequest('/plugin/sync', { method: 'POST' });
}

export const SYNC_STATUS_RETRY_LIMIT = 10;

export const syncStatusDelay = (retryCount) => new Promise((resolve) => setTimeout(resolve, 10 * 2 ** retryCount));

export async function getPluginSyncStatus() {
  return await makeRequest(`/plugin/sync`, { method: 'GET' });
}

export async function installPlugin() {
  const grafanaToken = await createGrafanaToken();
  await updateGrafanaToken(grafanaToken.key);
  return await makeRequest('/plugin/install', { method: 'POST' });
}
