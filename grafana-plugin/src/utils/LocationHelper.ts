import { KeyValue } from '@grafana/data';
import { locationService } from '@grafana/runtime';

import { getQueryParams } from 'plugin/GrafanaPluginRootPage.helpers';

class LocationHelper {
  update(params: KeyValue, method: 'replace' | 'push' | 'partial') {
    const queryParams = getQueryParams();

    const sortedExistingParams = sort(queryParams);
    const sortedNewParams = sort(params);

    if (getPathFromQueryParams(sortedExistingParams) !== getPathFromQueryParams(sortedNewParams)) {
      if (method === 'partial') {
        locationService.partial(params);
      } else {
        locationService[method](getPathFromQueryParams(sortedNewParams));
      }
    }
  }
}

function getPathFromQueryParams(queryParams) {
  return Object.keys(queryParams)
    .map((key) => `${key}=${queryParams[key]}`)
    .reduce((result, param, index) => {
      const delimitator = `${index > 0 ? '&' : ''}`;
      return `${result}${delimitator}${param}`;
    }, '?');
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
