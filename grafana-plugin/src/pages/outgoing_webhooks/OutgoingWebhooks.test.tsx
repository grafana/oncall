import 'jest/matchMedia.ts';
import { describe, expect, test } from '@jest/globals';
import { render, fireEvent, screen } from '@testing-library/react';

import React from 'react';

import '@testing-library/jest-dom';
import { OutgoingWebhooks } from './OutgoingWebhooks';

import outgoingWebhooksStub from 'jest/outgoingWebhooksStub';
import { mockGrafanaLocationSrv, mockUseStore } from 'jest/utils';
import { OutgoingWebhook } from 'models/outgoing_webhook/outgoing_webhook.types';

jest.mock('state/useStore', () => ({
  useStore: () => ({
    isUserActionAllowed: jest.fn().mockReturnValue(true),
  }),
}));
jest.mock('@grafana/runtime', () => ({
  getLocationSrv: jest.fn(),
}));

describe('OutgoingWebhooks', () => {
  const outgoingWebhooks = outgoingWebhooksStub as OutgoingWebhook[];

  const storeMock = {
    isUserActionAllowed: jest.fn().mockReturnValue(true),
    outgoingWebhookStore: {
      loadItem: () => Promise.resolve(outgoingWebhooks[0]),
      updateItems: () => Promise.resolve(),
      getSearchResult: () => outgoingWebhooks,
      items: outgoingWebhooks
    },
  };

  test('It renders all retrieved webhooks', async () => {
    render(<OutgoingWebhooks {...getProps()} />);

    const gTable = screen.queryByTestId('test__gTable');
    const rows = gTable.querySelectorAll('tbody tr');

    expect(getEditForm()).toBeNull(); // edit doesn't show for [id=undefined]
    expect(rows.length).toBe(outgoingWebhooks.length);
  });

  test('It opens Edit View if [id] is supplied', async () => {
    const id = outgoingWebhooks[0].id;
    render(<OutgoingWebhooks {...getProps(id)} />);

    expect(getEditForm()).toBeDefined(); // edit shows for [id=?]
  });

  function getProps(id: OutgoingWebhook['id'] = undefined): any {
    return { store: storeMock, query: { id } };
  }

  function getEditForm(): HTMLElement {
    return screen.queryByTestId('test__outgoingWebhookEditForm');
  }
});
