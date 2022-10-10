import 'jest/matchMedia.ts';
import { describe, expect, test } from '@jest/globals';
import { render, fireEvent, screen } from '@testing-library/react';

import React from 'react';

import '@testing-library/jest-dom';
import { OutgoingWebhooks } from './OutgoingWebhooks';

jest.mock('state/useStore', () => ({
  useStore: () => ({
    isUserActionAllowed: jest.fn().mockReturnValue(true),
  }),
}));

jest.mock('@grafana/runtime', () => ({
  getLocationSrv: jest.fn(),
}));

const storeMock = {
  isUserActionAllowed: jest.fn().mockReturnValue(true),
  outgoingWebhookStore: {
    loadItem: () => Promise.resolve(undefined),
    updateItems: jest.fn(),
    getSearchResult: jest.fn(),
  },
};

describe('OutgoingWebhooks', () => {
  function getProps(): any {
    return { store: storeMock, query: { id: undefined } };
  }

  test('It renders', async () => {
    render(<OutgoingWebhooks {...getProps()} />);
  });
});
