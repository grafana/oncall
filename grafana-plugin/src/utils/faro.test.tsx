import 'jest/matchMedia.ts';
import { describe, test } from '@jest/globals';

import FaroHelper from 'utils/faro';

import '@testing-library/jest-dom';
import { ONCALL_DEV, ONCALL_OPS, ONCALL_PROD } from './consts';

const ErrorMock = jest.spyOn(window, 'Error');

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
  beforeEach(() => {
    jest.clearAllMocks();

    FaroHelper.faro = undefined;
  });

  test.each([ONCALL_DEV, ONCALL_OPS, ONCALL_PROD])('It initializes faro for environment %s', (onCallApiUrl) => {
    const faro = FaroHelper.initializeFaro(onCallApiUrl);
    expect(faro).toBeDefined();
    expect(ErrorMock).not.toHaveBeenCalled();
  });

  test.each(['https://test.com', 'http://localhost:3000'])(
    'It fails initializing for dummy environment values',
    (onCallApiUrl) => {
      const faro = FaroHelper.initializeFaro(onCallApiUrl);
      expect(faro).toBeUndefined();
    }
  );

  test('It does not reinitialize faro instance if already initialized', () => {
    const instance = FaroHelper.initializeFaro(ONCALL_DEV);
    expect(instance).toBeDefined();

    const result = FaroHelper.initializeFaro(ONCALL_PROD);
    expect(result).toBeUndefined();
    expect(FaroHelper.faro).toBe(instance);
  });

  test('Initializer throws error for wrong env value', () => {
    const faro = FaroHelper.initializeFaro('https://test.com');
    expect(ErrorMock).toHaveBeenCalledWith(`No match found for given onCallApiUrl = https://test.com`);
    expect(faro).toBeUndefined();
  });
});
