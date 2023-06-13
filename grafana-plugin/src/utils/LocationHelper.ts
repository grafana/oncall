import { KeyValue } from '@grafana/data';
import { locationService } from '@grafana/runtime';

import { getQueryParams } from 'plugin/GrafanaPluginRootPage.helpers';

class LocationHelper {
  update(params: KeyValue, method: 'replace' | 'push' | 'partial') {
    const queryParams = getQueryParams();

    const sortedExistingParams = sort(queryParams);
    const sortedNewParams = sort(params);

    if (toQueryString(sortedExistingParams) !== toQueryString(sortedNewParams)) {
      if (method === 'partial') {
        locationService.partial(params);
      } else {
        locationService[method](toQueryString(sortedNewParams));
      }
    }
  }
}

function toQueryString(queryParams: KeyValue) {
  const urlParams = new URLSearchParams(queryParams);
  for (const [key, value] of Object.entries(queryParams)) {
    if (Array.isArray(value)) {
      urlParams.delete(key);
      value.forEach((v) => urlParams.append(key, v));
    }
  }
  return urlParams.toString();
}

function sort(object: KeyValue) {
  return Object.keys(object)
    .sort()
    .reduce((obj, key) => {
      obj[key] = object[key];
      return obj;
    }, {});
}

export default new LocationHelper();
