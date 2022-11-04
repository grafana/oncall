import { PluginPageProps, PluginPage as RealPluginPage } from '@grafana/runtime';

import { isNewNavigation } from 'plugin/GrafanaPluginRootPage.helpers';

export const PluginPage = (
  isNewNavigation() ? RealPluginPage : PluginPageFallback
) as React.ComponentType<PluginPageProps>;

function PluginPageFallback(props: PluginPageProps): React.ReactNode {
  return props.children;
}
