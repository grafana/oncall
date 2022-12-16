import { Faro } from '@grafana/faro-core';
import { initializeFaro, getWebInstrumentations } from '@grafana/faro-web-sdk';
import { TracingInstrumentation } from '@grafana/faro-web-tracing';
import { DocumentLoadInstrumentation } from '@opentelemetry/instrumentation-document-load';
import { FetchInstrumentation } from '@opentelemetry/instrumentation-fetch';
import { UserInteractionInstrumentation } from '@opentelemetry/instrumentation-user-interaction';
import { XMLHttpRequestInstrumentation } from '@opentelemetry/instrumentation-xml-http-request';

import plugin from '../../package.json'; // eslint-disable-line

const IGNORE_URLS = [/^((?!\/{0,1}a\/grafana\-oncall\-app\\).)*$/];

class FaroHelper {
  faro: Faro;

  initializeFaro() {
    const { faro: faroConfig } = plugin as any;

    if (!faroConfig.enabled || this.faro) {
      return;
    }

    try {
      this.faro = initializeFaro({
        url: faroConfig.url,
        apiKey: faroConfig.apiKey,
        isolate: true,
        instrumentations: [
          ...getWebInstrumentations({
            captureConsole: true,
          }),
          new TracingInstrumentation({
            instrumentations: [
              new DocumentLoadInstrumentation(),
              new FetchInstrumentation({ ignoreUrls: IGNORE_URLS }),
              new XMLHttpRequestInstrumentation({}),
              new UserInteractionInstrumentation(),
            ],
          }),
        ],
        session: (window as any).__PRELOADED_STATE__?.faro?.session,
        app: {
          name: 'Grafana OnCall',
          version: plugin?.version,
        },
      });

      this.faro.api.pushLog(['Faro was initialized for Grafana OnCall']);
    } catch (ex) {}
  }
}

export default new FaroHelper();
