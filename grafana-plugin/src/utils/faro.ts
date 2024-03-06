import { Faro, initializeFaro, LogLevel, InternalLoggerLevel, getWebInstrumentations } from '@grafana/faro-web-sdk';

import plugin from '../../package.json'; // eslint-disable-line
import {
  FARO_ENDPOINT_DEV,
  FARO_ENDPOINT_OPS,
  FARO_ENDPOINT_PROD,
  ONCALL_DEV,
  ONCALL_OPS,
  ONCALL_PROD,
} from './consts';

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

class BaseFaroHelper {
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
            captureConsoleDisabledLevels: [LogLevel.TRACE, LogLevel.ERROR],
          }),
        ],
        internalLoggerLevel: InternalLoggerLevel.VERBOSE,
        app: {
          name: appName,
          version: plugin?.version,
        },
        sessionTracking: {
          persistent: true,
        },
        beforeSend: (event) => {
          if ((event.meta.page?.url ?? '').includes('grafana-oncall-app')) {
            return event;
          }

          return null;
        },
      };

      this.faro = initializeFaro(faroOptions);

      this.faro.api.pushLog([`Faro was initialized for ${appName}`]);
    } catch (ex) {}

    return this.faro;
  }
}

export const FaroHelper = new BaseFaroHelper();
