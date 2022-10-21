import { locationService } from '@grafana/runtime';

class LocationHelper {
  update(params, method: 'replace' | 'push') {
    const existingQueryParams = locationService.getSearchObject();

    const sortedExistingParams = sort(existingQueryParams);
    const sortedNewParams = sort(params);

    if (getPathFromQueryParams(sortedExistingParams) !== getPathFromQueryParams(sortedNewParams)) {
      locationService[method](getPathFromQueryParams(sortedNewParams));
    }
  }
}

function getPathFromQueryParams(queryParams) {
  return Object.keys(queryParams).map(key => `${key}=${queryParams[key]}`).reduce((result, param, index) => {
    const delimitator = `${index > 0 ? '&' : ''}`;
    return `${result}${delimitator}${param}`;
  }, '?');
}

function sort(object) {
  return Object.keys(object)
    .sort()
    .reduce((obj, key) => {
      obj[key] = object[key];
      return obj;
    }, {});
}

export default new LocationHelper();
