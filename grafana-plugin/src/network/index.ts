import axios from 'axios';
import qs from 'query-string';

export const API_HOST = `${window.location.protocol}//${window.location.host}/`;
export const API_PROXY_PREFIX = 'api/plugin-proxy/grafana-oncall-app';
export const API_PATH_PREFIX = '/api/internal/v1';

const instance = axios.create();

instance.interceptors.request.use(function (config) {
  // Do something before request is sent
  config.paramsSerializer = (params) => {
    return qs.stringify(params, { arrayFormat: 'none' });
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
}

const failPaths = [
  'api/plugin-proxy/grafana-oncall-app/api/internal/v1/users/URPAN2A31CVWQ/',
  'api/plugin-proxy/grafana-oncall-app/api/internal/v1/escalation_chains/FDF7ZQMNKYIQK/',
];

export const makeRequest = async (path: string, config: RequestConfig) => {
  const { method = 'GET', params, data, validateStatus } = config;

  const url = `${API_PROXY_PREFIX}${API_PATH_PREFIX}${path}`;

  if (failPaths.includes(url)) {
    throw {
      response: {
        status: 403,
        data: {
          error_code: 'wrong_team',
          owner_team: {
            name: 'Rares',
            id: '14999718',
          },
        },
      },
    };
  }

  const response = await instance({
    method,
    url,
    params,
    data,
    validateStatus,
  });

  return response.data;
};
