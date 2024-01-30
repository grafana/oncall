import { config } from '@grafana/runtime';

export function isTopNavbar(): boolean {
  return !!config.featureToggles.topnav;
}

export function getGrafanaVersion(): { major?: number; minor?: number; patch?: number } {
  const regex = /^([1-9]?[0-9]*)\.([1-9]?[0-9]*)\.([1-9]?[0-9]*)/;
  const match = config.buildInfo.version.match(regex);

  if (match) {
    return {
      major: Number(match[1]),
      minor: Number(match[2]),
      patch: Number(match[3]),
    };
  }

  return {};
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
