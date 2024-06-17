import { Faro, initializeFaro, LogLevel, getWebInstrumentations, BrowserConfig } from '@grafana/faro-web-sdk';
import { AxiosResponse } from 'axios';

import plugin from '../../package.json'; // eslint-disable-line
import {
  FARO_ENDPOINT_DEV,
  FARO_ENDPOINT_OPS,
  FARO_ENDPOINT_PROD,
  ONCALL_DEV,
  ONCALL_OPS,
  ONCALL_PROD,
} from './consts';
import { safeJSONStringify } from './string';

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

      const faroOptions: BrowserConfig = {
        url: url,
        isolate: true,
        instrumentations: [
          ...getWebInstrumentations({
            captureConsoleDisabledLevels: [LogLevel.TRACE, LogLevel.ERROR],
          }),
        ],
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

  pushReactError = (error: Error) => {
    this.faro?.api.pushError(error, { context: { type: 'react' } });
  };

  pushNetworkRequestEvent = (config: { method: string; url: string; body: string }) => {
    this.faro?.api.pushEvent('Request sent', config);
  };

  pushFetchNetworkResponseEvent = ({ name, res, method }: { name: string; res: Response; method: string }) => {
    this.faro?.api.pushEvent(name, {
      method,
      url: res.url,
      status: `${res.status}`,
      statusText: `${res.statusText}`,
    });
  };

  pushFetchNetworkError = ({ res, responseData, method }: { res: Response; responseData: unknown; method: string }) => {
    this.faro?.api.pushError(new Error(`Network error: ${res.status}`), {
      context: {
        method,
        type: 'network',
        url: res.url,
        data: `${safeJSONStringify(responseData)}`,
        status: `${res.status}`,
        statusText: `${res.statusText}`,
        timestamp: new Date().toUTCString(),
      },
    });
  };

  pushAxiosNetworkResponseEvent = ({ name, res }: { name: string; res?: AxiosResponse }) => {
    this.faro?.api.pushEvent(name, {
      url: res?.config?.url,
      status: `${res?.status}`,
      statusText: `${res?.statusText}`,
      method: res?.config?.method.toUpperCase(),
    });
  };

  pushAxiosNetworkError = (res?: AxiosResponse) => {
    this.faro?.api.pushError(new Error(`Network error: ${res?.status}`), {
      context: {
        url: res?.config?.url,
        type: 'network',
        data: `${safeJSONStringify(res.data)}`,
        status: `${res?.status}`,
        statusText: `${res?.statusText}`,
        timestamp: new Date().toUTCString(),
      },
    });
  };
}

export const FaroHelper = new BaseFaroHelper();
