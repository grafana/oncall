import { PluginPageProps, PluginPage as RealPluginPage, config } from '@grafana/runtime';

export const PluginPage = RealPluginPage && (config.featureToggles.topnav ? RealPluginPage : PluginPageFallback) as any;

function PluginPageFallback(props: PluginPageProps): React.ReactNode {
  return props.children;
}