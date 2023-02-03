import { SpanStatusCode } from '@opentelemetry/api';
import { SemanticAttributes } from '@opentelemetry/semantic-conventions';
import axios from 'axios';
import qs from 'query-string';

import FaroHelper from 'utils/faro';

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

export const isNetworkError = axios.isAxiosError;

export const makeRequest = async <RT = any>(path: string, config: RequestConfig) => {
  const { method = 'GET', params, data, validateStatus } = config;

  const url = `${API_PROXY_PREFIX}${API_PATH_PREFIX}${path}`;
  const otel = FaroHelper.faro?.api?.getOTEL();

  if (FaroHelper.faro && otel) {
    const tracer = otel.trace.getTracer('default');
    let span = otel.trace.getActiveSpan();

    if (!span) {
      span = tracer.startSpan('http-request');
      span.setAttribute('page_url', document.URL.split('//')[1]);
      span.setAttribute(SemanticAttributes.HTTP_URL, url);
      span.setAttribute(SemanticAttributes.HTTP_METHOD, method);
    }

    return new Promise<RT>((resolve, reject) => {
      otel.context.with(otel.trace.setSpan(otel.context.active(), span), async () => {
        FaroHelper.faro.api.pushEvent('Sending request', { url });

        instance({
          method,
          url,
          params,
          data,
          validateStatus,
        })
          .then((response) => {
            FaroHelper.faro.api.pushEvent('Request completed', { url });
            span.end();
            resolve(response.data as RT);
          })
          .catch((ex) => {
            FaroHelper.faro.api.pushEvent('Request failed', { url });
            FaroHelper.faro.api.pushError(ex);
            span.setStatus({ code: SpanStatusCode.ERROR });
            span.end();
            reject(ex);
          });
      });
    });
  }

  return instance({
    method,
    url,
    params,
    data,
    validateStatus,
  })
    .then((response) => {
      FaroHelper.faro?.api.pushEvent('Request completed', { url });
      return response.data as RT;
    })
    .catch((ex) => {
      FaroHelper.faro?.api.pushEvent('Request failed', { url });
      FaroHelper.faro?.api.pushError(ex);
      return Promise.reject(ex);
    });
};
