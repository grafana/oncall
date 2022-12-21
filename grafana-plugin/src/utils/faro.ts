import { Faro } from '@grafana/faro-core';
import { initializeFaro, getWebInstrumentations } from '@grafana/faro-web-sdk';
import { TracingInstrumentation } from '@grafana/faro-web-tracing';
import { DocumentLoadInstrumentation } from '@opentelemetry/instrumentation-document-load';
import { FetchInstrumentation } from '@opentelemetry/instrumentation-fetch';
import { UserInteractionInstrumentation } from '@opentelemetry/instrumentation-user-interaction';
import { XMLHttpRequestInstrumentation } from '@opentelemetry/instrumentation-xml-http-request';

import plugin from '../../package.json'; // eslint-disable-line

const IGNORE_URLS = [/^((?!\/{0,1}a\/grafana\-oncall\-app\\).)*$/];

interface FaroConfig {
  url: string;
  apiKey: string;
  enabled: boolean;
  environment: string;
}

const ONCALL = 'Grafana OnCall';

class FaroHelper {
  faro: Faro;

  initializeFaro() {
    const faroInput = process.env || {};
    const FARO_ENV = faroInput['FARO_ENV'];
    const faroConfig: FaroConfig = {
      url: faroInput['FARO_URL'],
      apiKey: faroInput['FARO_API_KEY'],
      enabled: faroInput['FARO_ENABLED']?.toLowerCase() === 'true',
      environment: FARO_ENV ? `${ONCALL} ${FARO_ENV}` : ONCALL,
    };

    if (!faroConfig?.enabled || !faroConfig?.url || this.faro) {
      return undefined;
    }

    try {
      const faroOptions = {
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
          name: faroConfig.environment,
          version: plugin?.version,
        },
      };

      if (!faroConfig.apiKey) {
        delete faroOptions.apiKey; // appo11y has the key in the API instead
      }

      this.faro = initializeFaro(faroOptions);

      this.faro.api.pushLog([`Faro was initialized for ${faroConfig.environment}`]);
    } catch (ex) {}

    return this.faro;
  }
}

export default new FaroHelper();
