import { SpanStatusCode } from '@opentelemetry/api';
import { SemanticAttributes } from '@opentelemetry/semantic-conventions';
import createClient from 'openapi-fetch';
import qs from 'query-string';

import FaroHelper from 'utils/faro';

import { paths } from './autogenerated-api.types';

export const API_PROXY_PREFIX = 'api/plugin-proxy/grafana-oncall-app';
export const API_PATH_PREFIX = '/api/internal/v1';

export const customFetch = async (url: string, requestConfig: Parameters<typeof fetch>[1] = {}): Promise<Response> => {
  const { faro } = FaroHelper;
  const otel = faro?.api?.getOTEL();

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

        try {
          const response = await fetch(url, {
            ...requestConfig,
            headers: {
              ...requestConfig.headers,
              /**
               * In short, this header will tell the Grafana plugin proxy, a Go service which use Go's HTTP Transport,
               * to retry POST requests (and other non-idempotent requests). This doesn't necessarily make these requests
               * idempotent, but it will make them retry-able from Go's (read: net/http) perspective.
               *
               * https://stackoverflow.com/questions/42847294/how-to-catch-http-server-closed-idle-connection-error/62292758#62292758
               * https://raintank-corp.slack.com/archives/C01C4K8DETW/p1692280544382739?thread_ts=1692279329.797149&cid=C01C4K8DETW
               */ 'X-Idempotency-Key': `${Date.now()}-${Math.random()}`,
            },
          });
          faro.api.pushEvent('Request completed', { url });
          span.end();
          resolve(response);
        } catch (error) {
          faro.api.pushEvent('Request failed', { url });
          faro.api.pushError(error);
          span.setStatus({ code: SpanStatusCode.ERROR });
          span.end();
          reject(error);
        }
      });
    });
  } else {
    try {
      const response = await fetch(url, requestConfig);
      faro?.api.pushEvent('Request completed', { url });
      return response;
    } catch (error) {
      faro?.api.pushEvent('Request failed', { url });
      faro?.api.pushError(error);
      throw new Error(error);
    }
  }
};

const httpClient = createClient<paths>({
  baseUrl: `${API_PROXY_PREFIX}${API_PATH_PREFIX}`,
  querySerializer: (params: unknown) => qs.stringify(params, { arrayFormat: 'none' }),
  fetch: customFetch,
});

export default httpClient;
