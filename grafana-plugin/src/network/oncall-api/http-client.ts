import { SpanStatusCode } from '@opentelemetry/api';
import { SemanticAttributes } from '@opentelemetry/semantic-conventions';
import createClient from 'openapi-fetch';
import qs from 'query-string';

import { FaroHelper } from 'utils/faro';
import { formatBackendError, openErrorNotification } from 'utils/utils';

import { paths } from './autogenerated-api.types';

export const API_PROXY_PREFIX = 'api/plugin-proxy/grafana-oncall-app';
export const API_PATH_PREFIX = '/api/internal/v1';

const showApiError = (errorResponse: Response) => {
  if (errorResponse.status >= 400 && errorResponse.status < 500) {
    const text = formatBackendError(errorResponse.statusText);
    openErrorNotification(text);
  }
};

export const getCustomFetchFn =
  ({ withGlobalErrorHandler }: { withGlobalErrorHandler: boolean }) =>
  async (url: string, reqConfig: Parameters<typeof fetch>[1] = {}): Promise<Response> => {
    const { faro } = FaroHelper;
    const otel = faro?.api?.getOTEL();
    const requestConfig = {
      ...reqConfig,
      headers: {
        ...reqConfig.headers,
        'Content-Type': 'application/json',
        /**
         * In short, this header will tell the Grafana plugin proxy, a Go service which use Go's HTTP Transport,
         * to retry POST requests (and other non-idempotent requests). This doesn't necessarily make these requests
         * idempotent, but it will make them retry-able from Go's (read: net/http) perspective.
         *
         * https://stackoverflow.com/questions/42847294/how-to-catch-http-server-closed-idle-connection-error/62292758#62292758
         * https://raintank-corp.slack.com/archives/C01C4K8DETW/p1692280544382739?thread_ts=1692279329.797149&cid=C01C4K8DETW
         */ 'X-Idempotency-Key': `${Date.now()}-${Math.random()}`,
      },
    };

    if (faro && otel) {
      const tracer = otel.trace.getTracer('default');
      let span = otel.trace.getActiveSpan();

      if (!span) {
        span = tracer.startSpan('http-request');
        span.setAttribute('page_url', document.URL.split('//')[1]);
        span.setAttribute(SemanticAttributes.HTTP_URL, url);
        span.setAttribute(SemanticAttributes.HTTP_METHOD, requestConfig.method);
      }

      return new Promise((resolve, reject) => {
        otel.context.with(otel.trace.setSpan(otel.context.active(), span), async () => {
          faro.api.pushEvent('Sending request', { url });

          const res = await fetch(url, requestConfig);

          if (res.ok) {
            faro.api.pushEvent('Request completed', { url });
            span.end();
            resolve(res);
          } else {
            const errorData = await res.json();
            faro.api.pushEvent('Request failed', { url });
            faro.api.pushError(errorData);
            span.setStatus({ code: SpanStatusCode.ERROR });
            span.end();
            if (withGlobalErrorHandler) {
              showApiError(res);
            }
            reject(errorData);
          }
        });
      });
    } else {
      const res = await fetch(url, requestConfig);
      if (res.ok) {
        faro?.api.pushEvent('Request completed', { url });
        return res;
      } else {
        const errorData = await res.json();
        faro?.api.pushEvent('Request failed', { url });
        faro?.api.pushError(errorData);
        if (withGlobalErrorHandler) {
          showApiError(res);
        }
        throw errorData;
      }
    }
  };

const clientConfig = {
  baseUrl: `${API_PROXY_PREFIX}${API_PATH_PREFIX}`,
  querySerializer: (params: unknown) => qs.stringify(params, { arrayFormat: 'none' }),
};

// We might want to switch to middleware instead of 2 clients once this is published: https://github.com/drwpow/openapi-typescript/pull/1521
const onCallApiWithGlobalErrorHandling = createClient<paths>({
  ...clientConfig,
  fetch: getCustomFetchFn({ withGlobalErrorHandler: true }),
});
const onCallApiSkipErrorHandling = createClient<paths>({
  ...clientConfig,
  fetch: getCustomFetchFn({ withGlobalErrorHandler: false }),
});

export const onCallApi = ({ skipErrorHandling = false }: { skipErrorHandling?: boolean } = {}) =>
  skipErrorHandling ? onCallApiSkipErrorHandling : onCallApiWithGlobalErrorHandling;
