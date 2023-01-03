import { Faro, initializeFaro, getWebInstrumentations } from '@grafana/faro-web-sdk';
import { TracingInstrumentation } from '@grafana/faro-web-tracing';
import { DocumentLoadInstrumentation } from '@opentelemetry/instrumentation-document-load';
import { FetchInstrumentation } from '@opentelemetry/instrumentation-fetch';
import { UserInteractionInstrumentation } from '@opentelemetry/instrumentation-user-interaction';
import { XMLHttpRequestInstrumentation } from '@opentelemetry/instrumentation-xml-http-request';

import plugin from '../../package.json'; // eslint-disable-line

const IGNORE_URLS = [/^((?!\/{0,1}a\/grafana\-oncall\-app\\).)*$/];

interface FaroConfig {
  url: string;
  enabled: boolean;
  environment: string;
}

class FaroHelper {
  faro: Faro;

  initializeFaro(onCallApiUrl: string) {
    const faroConfig: FaroConfig = {
      url: 'https://faro-collector-prod-us-central-0.grafana.net/collect/f3a038193e7802cf47531ca94cfbada7',
      enabled: false,
      environment: undefined,
    };

    if (onCallApiUrl === 'https://oncall-prod-us-central-0.grafana.net/oncall') {
      faroConfig.enabled = true;
      faroConfig.environment = 'prod';
    } else if (onCallApiUrl === 'https://oncall-ops-us-east-0.grafana.net/oncall') {
      faroConfig.enabled = true;
      faroConfig.environment = 'ops';
    } else if (onCallApiUrl === 'https://oncall-dev-us-central-0.grafana.net/oncall') {
      faroConfig.enabled = true;
      faroConfig.environment = 'dev';
    } else {
      // This opensource, don't send traces
      /* faroConfig.enabled = true;
      faroConfig.environment = 'local'; */
    }

    if (!faroConfig?.enabled || !faroConfig?.url || this.faro) {
      return undefined;
    }

    try {
      const faroOptions = {
        url: faroConfig.url,
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
          name: 'grafana-oncall-test',
          version: plugin?.version,
          environment: faroConfig.environment,
        },
      };

      this.faro = initializeFaro(faroOptions);

      this.faro.api.pushLog([`Faro was initialized for ${faroConfig.environment}`]);
    } catch (ex) {}

    return this.faro;
  }
}

export default new FaroHelper();
