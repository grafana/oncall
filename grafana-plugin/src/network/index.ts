import { faro } from '@grafana/faro-react';
import { SpanStatusCode } from '@opentelemetry/api';
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

export const makeRequest = async <RT = any>(path: string, config: RequestConfig) => {
  const { method = 'GET', params, data, validateStatus } = config;

  const url = `${API_PROXY_PREFIX}${API_PATH_PREFIX}${path}`;

  const otel = faro.api.getOTEL();

  if (otel) {
    const tracer = otel.trace.getTracer('default');
    let span = otel.trace.getActiveSpan() ?? tracer.startSpan('http-request');

    return new Promise<RT>((resolve, reject) => {
      otel.context.with(otel.trace.setSpan(otel.context.active(), span), async () => {
        faro.api.pushEvent('Sending request', { url });

        try {
          const response = await instance({
            method,
            url,
            params,
            data,
            validateStatus,
          });

          faro.api.pushEvent('Request completed', { url });

          resolve(response.data as RT);
        } catch (ex) {
          faro.api.pushEvent('Request failed', { url });
          faro.api.pushError(ex);

          span.setStatus({ code: SpanStatusCode.ERROR });
          reject(ex);
        } finally {
          span.end();
        }
      });
    });
  }

  try {
    const response = await instance({
      method,
      url,
      params,
      data,
      validateStatus,
    });

    faro.api.pushEvent('Request completed', { url });

    return response.data as RT;
  } catch (ex) {
    faro.api.pushEvent('Request failed', { url });
    faro.api.pushError(ex);
    throw ex;
  }
};
