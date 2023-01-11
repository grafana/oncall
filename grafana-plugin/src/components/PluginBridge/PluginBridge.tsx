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
  notInstalledComponent?: ReactElement;
  // shows an optional component when we're checking if the plugin is installed
  loadingComponent?: ReactElement;
  children?: ReactElement;
}

export const PluginBridge: FC<PluginBridgeProps> = ({ children, plugin }) => {
  const { loading, error, value } = useAsync(() => getPluginSettings(plugin, { showErrorAlert: false }));

  if (loading) {
    return null;
  }

  const installed = value && !error && !loading;
  const enabled = value?.enabled;

  if (!installed || !enabled) {
    return null;
  }

  return <>{children}</>;
};
