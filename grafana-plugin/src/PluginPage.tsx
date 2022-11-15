import { PluginPageProps, PluginPage as RealPluginPage } from '@grafana/runtime';

import { isTopNavbar } from 'plugin/GrafanaPluginRootPage.helpers';

export const PluginPage = (
  isTopNavbar() ? RealPluginPage : PluginPageFallback
) as React.ComponentType<PluginPageProps>;

function PluginPageFallback(props: PluginPageProps): React.ReactNode {
  return props.children;
}
