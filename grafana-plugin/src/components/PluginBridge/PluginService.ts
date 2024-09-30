import { PluginMeta } from '@grafana/data';
import { BackendSrvRequest, getBackendSrv } from '@grafana/runtime';

import { SupportedPlugin } from './PluginBridge';

type PluginId = SupportedPlugin | string;

const pluginCache = new Map<string, PluginMeta>();

export async function getPluginSettings(pluginId: PluginId, options?: Partial<BackendSrvRequest>): Promise<PluginMeta> {
  const pluginMetadata = pluginCache.get(pluginId);

  if (pluginMetadata) {
    return Promise.resolve(pluginMetadata);
  }

  try {
    const settings = await getBackendSrv().get<PluginMeta>(
      `/api/plugins/${pluginId}/settings`,
      undefined,
      undefined,
      options
    );
    pluginCache.set(pluginId, settings);
    return settings;
  } catch (err) {
    throw new Error('Unknown Plugin' + err);
  }
}
