import React, { FC, ReactElement } from 'react';

import { useAsync } from 'react-use';

import { getPluginSettings } from './PluginService';

export enum SupportedPlugin {
  Incident = 'grafana-incident-app',
  MachineLearning = 'grafana-ml-app',
}

export type PluginID = SupportedPlugin | string;

export interface PluginBridgeProps {
  plugin: PluginID;
  // shows an optional component when the plugin is not installed
  children?: ReactElement;
}

export const PluginBridge: FC<PluginBridgeProps> = ({ children, plugin }) => {
  const { error, value } = useAsync(() => getPluginSettings(plugin, { showErrorAlert: false }));
  const installed = value && !error;
  const enabled = value?.enabled;

  if (!installed || !enabled) {
    return null;
  }

  return <>{children}</>;
};
