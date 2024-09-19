/**
 * globally import this, avoids needing to import it in each file
 * https://stackoverflow.com/a/65871118
 */
import '@testing-library/jest-dom';

import 'plugin/dayjs';

import { TextEncoder, TextDecoder } from 'util';

jest.mock('@grafana/runtime', () => ({
  __esModule: true,
  config: {
    featureToggles: {
      topNav: false,
    },
    bootData: {
      user: {
        timezone: 'UTC',
      },
    },
  },
  getBackendSrv: jest.fn().mockImplementation(() => ({
    get: jest.fn(),
    post: jest.fn(),
  })),
  getLocationSrv: jest.fn(),
}));

Object.assign(global, { TextDecoder, TextEncoder });

// https://stackoverflow.com/a/66055672
// https://jestjs.io/docs/manual-mocks#mocking-methods-which-are-not-implemented-in-jsdom
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // Deprecated
    removeListener: jest.fn(), // Deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

Object.defineProperty(window, 'location', {
  configurable: true,
  value: { reload: jest.fn() },
});

Object.defineProperty(window, 'ResizeObserver', {
  writable: true,
  value: class ResizeObserver {
    constructor(callback: ResizeObserverCallback) {
      setTimeout(() => {
        callback(
          [
            {
              contentRect: {
                x: 1,
                y: 2,
                width: 500,
                height: 500,
                top: 100,
                bottom: 0,
                left: 100,
                right: 0,
              },
              target: {},
            } as ResizeObserverEntry,
          ],
          this
        );
      });
    }
    observe() {}
    disconnect() {}
    unobserve() {}
  },
});
