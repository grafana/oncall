import { FaroHelper } from 'utils/faro';

import { getCustomFetchFn } from './http-client';

jest.mock('utils/faro', () => ({
  __esModule: true,
  FaroHelper: {
    faro: {
      api: {
        getOTEL: jest.fn(() => undefined),
        pushEvent: jest.fn(),
        pushError: jest.fn(),
      },
    },
  },
}));
jest.mock('openapi-fetch', () => ({
  __esModule: true,
  default: () => {},
}));

const fetchMock = jest.fn().mockResolvedValue(true);

const HEADERS = new Headers();
HEADERS.set('Content-Type', 'application/json');
const REQUEST_CONFIG = {
  headers: HEADERS,
};
const URL = 'https://someurl.com';
const SUCCESSFUL_RESPONSE_MOCK = { ok: true };
const FAILING_RESPONSE_MOCK = {
  ok: false,
  json: () => 'ERROR',

  // we need to have clone available to actually clone the response
  clone: () => ({
    ok: false,
    json: () => 'ERROR',
  }),
};
const customFetch = getCustomFetchFn({ withGlobalErrorHandler: true });

describe('customFetch', () => {
  beforeAll(() => {
    Object.defineProperty(global, 'fetch', {
      writable: true,
      value: fetchMock,
    });
  });
  afterEach(jest.clearAllMocks);

  describe('if there is no otel', () => {
    describe('if response is successful', () => {
      it('should push event to faro and return response', async () => {
        fetchMock.mockResolvedValue(SUCCESSFUL_RESPONSE_MOCK);
        const response = await customFetch(URL, REQUEST_CONFIG);
        expect(FaroHelper.faro.api.pushEvent).toHaveBeenCalledWith('Request completed', { url: URL });
        expect(response).toEqual(SUCCESSFUL_RESPONSE_MOCK);
      });
    });

    describe('if response is not successful', () => {
      it('should push event and error to faro', async () => {
        (FaroHelper.faro.api.getOTEL as unknown as jest.Mock).mockReturnValueOnce(undefined);
        fetchMock.mockResolvedValueOnce(FAILING_RESPONSE_MOCK);
        await expect(customFetch(URL, REQUEST_CONFIG)).rejects.toEqual(FAILING_RESPONSE_MOCK);
        expect(FaroHelper.faro.api.pushEvent).toHaveBeenCalledWith('Request failed', { url: URL });
        expect(FaroHelper.faro.api.pushError).toHaveBeenCalledWith(FAILING_RESPONSE_MOCK.json());
      });
    });
  });

  describe('if there is otel', () => {
    const spanEndMock = jest.fn();
    const setAttributeMock = jest.fn();
    const spanStartMock = jest.fn(() => ({
      setAttribute: setAttributeMock,
      end: spanEndMock,
    }));
    const otel = {
      trace: {
        getTracer: () => ({
          startSpan: spanStartMock,
        }),
        getActiveSpan: jest.fn(),
        setSpan: jest.fn(),
      },
      context: {
        active: jest.fn(),
        with: (_ctx, fn) => {
          fn();
        },
      },
    };
    (FaroHelper.faro.api.getOTEL as unknown as jest.Mock).mockReturnValue(otel);

    it(`starts span if it doesn't exist`, async () => {
      otel.trace.getActiveSpan.mockReturnValueOnce(undefined);
      await customFetch(URL, REQUEST_CONFIG);
      expect(spanStartMock).toHaveBeenCalledTimes(1);
    });

    it(`passes request config`, async () => {
      await customFetch(URL, REQUEST_CONFIG);
      expect(fetchMock).toHaveBeenCalledWith(expect.any(String), REQUEST_CONFIG);
    });

    describe('if response is successful', () => {
      it('should push event to faro, end span and return response', async () => {
        fetchMock.mockResolvedValue(SUCCESSFUL_RESPONSE_MOCK);
        const response = await customFetch(URL, REQUEST_CONFIG);
        expect(FaroHelper.faro.api.pushEvent).toHaveBeenCalledWith('Request completed', { url: URL });
        expect(spanEndMock).toHaveBeenCalledTimes(1);
        expect(response).toEqual(SUCCESSFUL_RESPONSE_MOCK);
      });
    });

    describe('if response is not successful', () => {
      it('should reject Promise, push event to faro, set span status to error and end span', async () => {
        fetchMock.mockResolvedValueOnce(FAILING_RESPONSE_MOCK);
        await expect(customFetch(URL, REQUEST_CONFIG)).rejects.toEqual(FAILING_RESPONSE_MOCK);
        expect(FaroHelper.faro.api.pushEvent).toHaveBeenCalledWith('Request failed', { url: URL });
        expect(FaroHelper.faro.api.pushError).toHaveBeenCalledWith(FAILING_RESPONSE_MOCK.json());
        expect(spanEndMock).toHaveBeenCalledTimes(1);
      });
    });
  });
});
