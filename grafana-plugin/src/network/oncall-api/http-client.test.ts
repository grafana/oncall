import { FaroHelper } from 'utils/faro';

import { getCustomFetchFn } from './http-client';

jest.mock('utils/faro', () => ({
  __esModule: true,

  FaroHelper: {
    initializeFaro: jest.fn(),
    faro: {
      api: {
        pushEvent: jest.fn(),
        pushError: jest.fn(),
      },
    },
    pushFetchNetworkError: jest.fn(),
    pushNetworkRequestEvent: jest.fn(),
    pushFetchNetworkResponseEvent: jest.fn(),
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
  body: { a: 'a' } as unknown as BodyInit,
  method: 'GET',
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

  describe('if response is successful', () => {
    it('should push event to faro and return response', async () => {
      fetchMock.mockResolvedValue(SUCCESSFUL_RESPONSE_MOCK);
      const response = await customFetch(URL, REQUEST_CONFIG);
      expect(FaroHelper.pushNetworkRequestEvent).toHaveBeenCalledWith({
        body: JSON.stringify(REQUEST_CONFIG.body),
        method: REQUEST_CONFIG.method,
        url: URL,
      });
      expect(response).toEqual(SUCCESSFUL_RESPONSE_MOCK);
    });
  });

  describe('if response is not successful', () => {
    it('should push event and error to faro', async () => {
      fetchMock.mockResolvedValueOnce(FAILING_RESPONSE_MOCK);
      await expect(customFetch(URL, REQUEST_CONFIG)).rejects.toEqual(FAILING_RESPONSE_MOCK);
      expect(FaroHelper.pushNetworkRequestEvent).toHaveBeenCalledWith({
        body: JSON.stringify(REQUEST_CONFIG.body),
        method: REQUEST_CONFIG.method,
        url: URL,
      });
      expect(FaroHelper.pushFetchNetworkError).toHaveBeenCalledWith({
        method: REQUEST_CONFIG.method,
        responseData: 'ERROR',
        res: FAILING_RESPONSE_MOCK,
      });
    });
  });
});
