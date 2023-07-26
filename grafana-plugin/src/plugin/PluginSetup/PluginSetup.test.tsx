import React from 'react';

import * as runtime from '@grafana/runtime';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { RootBaseStore } from 'state/rootBaseStore';
import { useStore as useStoreOriginal } from 'state/useStore';

import PluginSetup, { PluginSetupProps } from '.';

jest.mock('state/useStore');

jest.mock('@grafana/runtime', () => ({
  __esModule: true,

  config: {
    featureToggles: {
      topnav: undefined,
    },
  },

  getBackendSrv: () => ({
    get: jest.fn(),
    post: jest.fn(),
  }),

  PluginPage: (props: any) => <>{props.children}</>,
}));

jest.mock('grafana/app/core/core', () => ({
  contextSrv: {
    user: {
      orgRole: null,
    },
    hasAccess: (_action, _fallback): boolean => null,
  },
}));

const createComponentAndMakeAssertions = async (rootBaseStore: RootBaseStore) => {
  // mocks
  const mockedSetupPlugin = jest.fn();
  rootBaseStore.setupPlugin = mockedSetupPlugin;
  (useStoreOriginal as jest.Mock<ReturnType<typeof useStoreOriginal>>).mockReturnValue(rootBaseStore);

  // test setup
  const MockedInitializedComponent = jest.fn().mockReturnValue(<div>hello</div>);

  const props = {
    meta: {
      jsonData: 'hello',
    },
    InitializedComponent: MockedInitializedComponent,
  } as unknown as PluginSetupProps;

  const component = render(<PluginSetup {...props} />);

  // assertions
  expect(mockedSetupPlugin).toHaveBeenCalledTimes(1);
  expect(mockedSetupPlugin).toHaveBeenCalledWith(props.meta);
  expect(component.container).toMatchSnapshot();

  return mockedSetupPlugin;
};

describe('PluginSetup', () => {
  afterEach(() => {
    jest.resetAllMocks();
  });

  test('app is loading', async () => {
    const rootBaseStore = new RootBaseStore();
    await createComponentAndMakeAssertions(rootBaseStore);
  });

  test('there is an error message', async () => {
    const rootBaseStore = new RootBaseStore();
    rootBaseStore.initializationError = 'ohhhh noo';
    await createComponentAndMakeAssertions(rootBaseStore);
  });

  test('there is an error message - retry setup', async () => {
    const rootBaseStore = new RootBaseStore();
    rootBaseStore.initializationError = 'ohhhh noo';

    const mockedSetupPlugin = await createComponentAndMakeAssertions(rootBaseStore);

    await userEvent.click(screen.getByText('Retry'));

    expect(mockedSetupPlugin).toHaveBeenCalledTimes(2);
  });

  test('currently undergoing maintenance', async () => {
    const rootBaseStore = new RootBaseStore();
    rootBaseStore.currentlyUndergoingMaintenance = true;
    rootBaseStore.initializationError = 'there is some sort of maintenance';
    await createComponentAndMakeAssertions(rootBaseStore);
  });

  test('app successfully initialized', async () => {
    const rootBaseStore = new RootBaseStore();
    rootBaseStore.initializationError = null;
    await createComponentAndMakeAssertions(rootBaseStore);
  });

  test.each([true, false])('app initialized with topnavbar = %s', async (isTopNavBar: boolean) => {
    runtime.config.featureToggles.topnav = isTopNavBar;

    const rootBaseStore = new RootBaseStore();
    await createComponentAndMakeAssertions(rootBaseStore);
  });
});
