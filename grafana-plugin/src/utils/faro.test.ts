import FaroHelper from 'utils/faro';

import 'jest/matchMedia.ts';

import { describe, test } from '@jest/globals';
import '@testing-library/jest-dom';

jest.mock('@grafana/faro-web-sdk', () => ({
  initializeFaro: jest.fn().mockReturnValue({
    api: {
      pushLog: jest.fn(),
    },
  }),
  getWebInstrumentations: () => [],
}));

jest.mock('@grafana/faro-web-tracing', () => ({
  TracingInstrumentation: jest.fn(),
}));
jest.mock('@opentelemetry/instrumentation-document-load', () => ({
  DocumentLoadInstrumentation: jest.fn(),
}));
jest.mock('@opentelemetry/instrumentation-fetch', () => ({
  FetchInstrumentation: jest.fn(),
}));

describe('Faro', () => {
  const OLD_ENV = process.env;

  beforeEach(() => {
    jest.resetModules();
    process.env = { ...OLD_ENV };
  });

  afterAll(() => {
    process.env = OLD_ENV;
  });

  const getProcessEnv = (
    config: { faroUrl?: string; apiKey?: string; enabled?: string } = {
      faroUrl: 'localhost:12345/collect',
      apiKey: 'secret',
      enabled: 'true',
    }
  ) => {
    const { faroUrl, apiKey, enabled } = config;

    return {
      FARO_URL: faroUrl,
      FARO_API_KEY: apiKey,
      FARO_ENABLED: enabled,
    };
  };

  test('It initializes faro ENABLED === true', () => {
    process.env = getProcessEnv();
    const faro = FaroHelper.initializeFaro();

    expect(faro).toBeDefined();
    expect(faro.api.pushLog).toHaveBeenCalledTimes(1);
  });

  test('It does not initialize faro if ENABLED != true', () => {
    process.env = getProcessEnv({ enabled: 'some-other-value-here' });
    const faro = FaroHelper.initializeFaro();
    expect(faro).toBeUndefined();
  });

  test('It skips initializing if values are missing', () => {
    let faro;

    process.env = getProcessEnv({ faroUrl: undefined });
    faro = FaroHelper.initializeFaro();
    expect(faro).toBeUndefined();

    process.env = getProcessEnv({ apiKey: undefined });
    faro = FaroHelper.initializeFaro();
    expect(faro).toBeUndefined();

    process.env = getProcessEnv({ enabled: undefined });
    faro = FaroHelper.initializeFaro();
    expect(faro).toBeUndefined();
  });
});
