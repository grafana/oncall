import axios, { AxiosError } from 'axios';
import { getOnCallApiPath } from 'helpers/consts';
import { FaroHelper } from 'helpers/faro';
import { safeJSONStringify } from 'helpers/string';
import qs from 'query-string';

const instance = axios.create();

instance.interceptors.request.use(function (config) {
  // Do something before request is sent
  config.paramsSerializer = {
    serialize: (params) => {
      return qs.stringify(params, { arrayFormat: 'none' });
    },
  };

  config.validateStatus = (status) => {
    return status >= 200 && status < 300; // default
  };

  return {
    ...config,
  };
});

interface RequestConfig {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'OPTIONS';
  params?: any;
  data?: any;
  withCredentials?: boolean;
  validateStatus?: (status: number) => boolean;
  headers?: {
    [key: string]: string | number;
  };
}

export const isNetworkError = axios.isAxiosError;

export const makeRequestRaw = async (path: string, config: RequestConfig = {}) => {
  const { method = 'GET', params, data, validateStatus, headers } = config;

  const url = getOnCallApiPath(path);

  try {
    FaroHelper.pushNetworkRequestEvent({ method, url, body: `${safeJSONStringify(data)}` });
    const response = await instance({
      method,
      url,
      params,
      data,
      validateStatus,
      headers,
    });

    FaroHelper.pushAxiosNetworkResponseEvent({ name: 'Request succeeded', res: response });
    return response;
  } catch (ex) {
    const error = ex as AxiosError;
    FaroHelper.pushAxiosNetworkResponseEvent({ name: 'Request failed', res: error.response });
    FaroHelper.pushAxiosNetworkError(error.response);
    throw ex;
  }
};

export const makeRequest = async <RT = any>(path: string, config: RequestConfig = {}) => {
  try {
    const result = await makeRequestRaw(path, config);
    return result.data as RT;
  } catch (ex) {
    throw ex;
  }
};
