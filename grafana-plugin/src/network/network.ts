import axios from 'axios';
import qs from 'query-string';

import { FaroHelper } from 'utils/faro';

export const API_PROXY_PREFIX = 'api/plugin-proxy/grafana-oncall-app';
export const API_PATH_PREFIX = '/api/internal/v1';

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

export const makeRequestRaw = async <RT = any>(path: string, config: RequestConfig) => {
  const { method = 'GET', params, data, validateStatus, headers } = config;

  const url = `${API_PROXY_PREFIX}${API_PATH_PREFIX}${path}`;

  FaroHelper.faro.api.pushEvent('Sending request', { url });

  try {
    const response = await instance({
      method,
      url,
      params,
      data,
      validateStatus,
      headers: {
        ...headers,
        /**
         * In short, this header will tell the Grafana plugin proxy, a Go service which use Go's HTTP Transport,
         * to retry POST requests (and other non-idempotent requests). This doesn't necessarily make these requests
         * idempotent, but it will make them retry-able from Go's (read: net/http) perspective.
         *
         * https://stackoverflow.com/questions/42847294/how-to-catch-http-server-closed-idle-connection-error/62292758#62292758
         * https://raintank-corp.slack.com/archives/C01C4K8DETW/p1692280544382739?thread_ts=1692279329.797149&cid=C01C4K8DETW
         */
        'X-Idempotency-Key': `${Date.now()}-${Math.random()}`,
      },
    });
    FaroHelper.faro.api.pushEvent('Request completed', { url });

    return response;
  } catch (ex) {
    FaroHelper.faro.api.pushEvent('Request failed', { url });
    FaroHelper.faro.api.pushError(ex);

    throw ex;
  }
};

export const makeRequest = async <RT = any>(path: string, config: RequestConfig) => {
  try {
    const result = await makeRequestRaw(path, config);
    return result.data as RT;
  } catch (ex) {
    throw ex;
  }
};
