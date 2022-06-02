import axios from 'axios';
import qs from 'query-string';

import plugin from '../../package.json'; // eslint-disable-line

// Send version header to all requests
axios.defaults.headers.common['X-OnCall-Plugin-Version'] = plugin?.version;

axios.interceptors.request.use(function (config) {
  // Do something before request is sent
  config.paramsSerializer = (params) => {
    return qs.stringify(params, { arrayFormat: 'none' });
  };

  return {
    ...config,
    withCredentials: true,
  };
});
