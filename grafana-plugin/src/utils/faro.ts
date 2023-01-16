import { Faro, initializeFaro, getWebInstrumentations } from '@grafana/faro-web-sdk';
import { TracingInstrumentation } from '@grafana/faro-web-tracing';
import { DocumentLoadInstrumentation } from '@opentelemetry/instrumentation-document-load';
import { FetchInstrumentation } from '@opentelemetry/instrumentation-fetch';
import { UserInteractionInstrumentation } from '@opentelemetry/instrumentation-user-interaction';
import { XMLHttpRequestInstrumentation } from '@opentelemetry/instrumentation-xml-http-request';

import plugin from '../../package.json'; // eslint-disable-line
import {
  FARO_ENDPOINT_DEV,
  FARO_ENDPOINT_OPS,
  FARO_ENDPOINT_PROD,
  ONCALL_DEV,
  ONCALL_OPS,
  ONCALL_PROD,
} from './consts';

const IGNORE_URLS = [/^((?!\/{0,1}a\/grafana\-oncall\-app\\).)*$/];

export function getAppNameUrlPair(onCallApiUrl: string): { appName: string; url: string } {
  const baseName = 'grafana-oncall';

  switch (onCallApiUrl) {
    case ONCALL_DEV:
      return { appName: `${baseName}-dev`, url: FARO_ENDPOINT_DEV };
    case ONCALL_OPS:
      return { appName: `${baseName}-ops`, url: FARO_ENDPOINT_OPS };
    case ONCALL_PROD:
      return { appName: `${baseName}-prod`, url: FARO_ENDPOINT_PROD };
    default:
      throw new Error(`No match found for given onCallApiUrl = ${onCallApiUrl}`);
  }
}

class FaroHelper {
  faro: Faro;

  initializeFaro(onCallApiUrl: string) {
    if (this.faro) {
      return undefined;
    }

    try {
      const { appName, url } = getAppNameUrlPair(onCallApiUrl);

      const faroOptions = {
        url: url,
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
          name: appName,
          version: plugin?.version,
        },
      };

      this.faro = initializeFaro(faroOptions);

      this.faro.api.pushLog([`Faro was initialized for ${appName}`]);
    } catch (ex) {}

    return this.faro;
  }
}

export default new FaroHelper();
