import { PluginPageProps, PluginPage as RealPluginPage, config, PluginPageType } from '@grafana/runtime';

export const PluginPage =
  RealPluginPage &&
  ((config.featureToggles.topnav ? RealPluginPage : PluginPageFallback) as React.ComponentType<PluginPageProps>);

function PluginPageFallback(props: PluginPageProps): React.ReactNode {
  return props.children;
}
