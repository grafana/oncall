import 'jest/matchMedia.ts';
import React from 'react';

import { describe, expect, test } from '@jest/globals';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import outgoingWebhooksStub from 'jest/outgoingWebhooksStub';
import { Provider } from 'mobx-react';
import { BrowserRouter, Switch } from 'react-router-dom';

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

const mockStoreMock = {
  outgoingWebhookStore: outgoingWebhookStore(),
  userStore: { currentUser: {} },
  grafanaTeamStore: { items: {}, updateItems: () => Promise.resolve({}) },
  filtersStore: { updateOptionsForPage: () => Promise.resolve([]), updateValuesForPage: () => {} },
};

jest.mock('@grafana/faro-web-sdk', () => ({
  initializeFaro: jest.fn(),
  TracingInstrumentation: undefined,
}));
jest.mock('@grafana/faro-web-tracing', () => ({
  TracingInstrumentation: undefined,
}));

jest.mock('plugin/GrafanaPluginRootPage.helpers', () => ({
  isTopNavbar: () => false,
  getQueryParams: () => ({}),
}));

jest.mock('@grafana/runtime', () => ({
  getBackendSrv: () => {},
  config: {
    featureToggles: {
      topNav: false,
    },
  },
}));

jest.mock('state/useStore', () => ({
  useStore: () => ({
    ...mockStoreMock,
  }),
}));

jest.mock('utils/authorization', () => ({
  ...jest.requireActual('utils/authorization'),
  isUserActionAllowed: jest.fn().mockReturnValue(true),
}));

jest.mock('@grafana/runtime', () => ({
  getLocationSrv: jest.fn(),
}));

describe('OutgoingWebhooks', () => {
  beforeAll(() => {
    console.warn = () => {};
    console.error = () => {};
  });

  test('It renders all retrieved webhooks', async () => {
    render(
      <Provider store={mockStoreMock}>
        <BrowserRouter>
          <Switch>
            <OutgoingWebhooks {...getProps()} />
          </Switch>
        </BrowserRouter>
      </Provider>
    );

    await waitFor(() => {
      const gTable = screen.queryByTestId('test__gTable');
      const rows = gTable.querySelectorAll('tbody tr');

      expect(() => queryEditForm()).toThrow(); // edit doesn't show for [id=undefined]
      expect(rows.length).toBe(outgoingWebhooks.length);
    });
  });

  test('It opens Edit View if [id] is supplied', async () => {
    const id = outgoingWebhooks[0].id;
    render(
      <Provider store={mockStoreMock}>
        <BrowserRouter>
          <Switch>
            <OutgoingWebhooks {...getProps(id)} />
          </Switch>
        </BrowserRouter>
      </Provider>
    );

    expect(() => queryEditForm()).toThrow(); // before updates kick in
    await waitFor(() => {
      expect(queryEditForm()).toBeDefined(); // edit shows for [id=?]
    });
  });

  function getProps(id: OutgoingWebhook['id'] = undefined): any {
    return { store: mockStoreMock, match: { params: { id } }, team: {} };
  }

  function queryEditForm(): HTMLElement {
    return screen.getByTestId<HTMLElement>('test__outgoingWebhookEditForm');
  }
});
