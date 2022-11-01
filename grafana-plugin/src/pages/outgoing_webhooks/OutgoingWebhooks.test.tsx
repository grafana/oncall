import 'jest/matchMedia.ts';
import React from 'react';

import { describe, expect, test } from '@jest/globals';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import outgoingWebhooksStub from 'jest/outgoingWebhooksStub';

import { OutgoingWebhook } from 'models/outgoing_webhook/outgoing_webhook.types';

import { OutgoingWebhooks } from 'pages/outgoing_webhooks/OutgoingWebhooks';

const outgoingWebhooks = outgoingWebhooksStub as OutgoingWebhook[];
const outgoingWebhookStore = () => ({
  loadItem: () => Promise.resolve(outgoingWebhooks[0]),
  updateItems: () => Promise.resolve(),
  getSearchResult: () => outgoingWebhooks,
  items: outgoingWebhooks.reduce((prev, current) => {
    prev[current.id] = current;
    return prev;
  }, {}),
});

jest.mock('@grafana/runtime', () => ({
  config: {
    featureToggles: {
      topNav: false
    },
  },
}));

jest.mock('state/useStore', () => ({
  useStore: () => ({
    outgoingWebhookStore: outgoingWebhookStore(),
    isUserActionAllowed: jest.fn().mockReturnValue(true),
  }),
}));

jest.mock('@grafana/runtime', () => ({
  getLocationSrv: jest.fn(),
}));

describe('OutgoingWebhooks', () => {
  const storeMock = {
    isUserActionAllowed: jest.fn().mockReturnValue(true),
    outgoingWebhookStore: outgoingWebhookStore(),
  };

  beforeAll(() => {
    console.warn = () => {};
    console.error = () => {};
  });

  test('It renders all retrieved webhooks', async () => {
    render(<OutgoingWebhooks {...getProps()} />);

    const gTable = screen.queryByTestId('test__gTable');
    const rows = gTable.querySelectorAll('tbody tr');

    await waitFor(() => {
      expect(() => queryEditForm()).toThrow(); // edit doesn't show for [id=undefined]
      expect(rows.length).toBe(outgoingWebhooks.length);
    });
  });

  test('It opens Edit View if [id] is supplied', async () => {
    const id = outgoingWebhooks[0].id;
    render(<OutgoingWebhooks {...getProps(id)} />);

    expect(() => queryEditForm()).toThrow(); // before updates kick in
    await waitFor(() => {
      expect(queryEditForm()).toBeDefined(); // edit shows for [id=?]
    });
  });

  function getProps(id: OutgoingWebhook['id'] = undefined): any {
    return { store: storeMock, query: { id } };
  }

  function queryEditForm(): HTMLElement {
    return screen.getByTestId<HTMLElement>('test__outgoingWebhookEditForm');
  }
});
