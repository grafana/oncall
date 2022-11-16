import { config } from '@grafana/runtime';

export function isTopNavbar(): boolean {
  return !!config.featureToggles.topnav;
}

export function getQueryParams(): any {
  const searchParams = new URLSearchParams(window.location.search);
  const result = {};
  for (const [key, value] of searchParams) {
    result[key] = value;
  }
  return result;
}
