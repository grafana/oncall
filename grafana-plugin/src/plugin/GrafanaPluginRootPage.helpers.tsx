import { config } from '@grafana/runtime';

export function isNewNavigation(): boolean {
  return !!config.featureToggles.topnav;
}
