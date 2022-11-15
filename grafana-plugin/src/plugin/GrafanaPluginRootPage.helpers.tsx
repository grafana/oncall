import { config } from '@grafana/runtime';

export function isTopNavbar(): boolean {
  return !!config.featureToggles.topnav;
}
