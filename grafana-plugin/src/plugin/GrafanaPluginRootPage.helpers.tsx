import { config } from '@grafana/runtime';

export function isTopNavbar(): boolean {
  return !!config.featureToggles.topnav;
}

export function getQueryParams(): any {
  const searchParams = new URLSearchParams(window.location.search);
  const result = {};
  for (const [key, value] of searchParams) {
    if (result[key]) {
      // key already existing, we're handling an array
      if (!Array.isArray(result[key])) {
        result[key] = new Array(result[key]);
      }

      result[key].push(value);
    } else {
      result[key] = value;
    }
  }

  return result;
}
