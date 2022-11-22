import React from 'react';

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { RootBaseStore } from 'state/rootBaseStore';
import { useStore as useStoreOriginal } from 'state/useStore';

import PluginSetup, { PluginSetupProps } from '.';

jest.mock('state/useStore');

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
    rootBaseStore.appLoading = true;
    await createComponentAndMakeAssertions(rootBaseStore);
  });

  test('there is an error message', async () => {
    const rootBaseStore = new RootBaseStore();
    rootBaseStore.appLoading = false;
    rootBaseStore.initializationError = 'ohhhh noo';
    await createComponentAndMakeAssertions(rootBaseStore);
  });

  test('there is an error message - retry setup', async () => {
    const rootBaseStore = new RootBaseStore();
    rootBaseStore.appLoading = false;
    rootBaseStore.initializationError = 'ohhhh noo';

    const mockedSetupPlugin = await createComponentAndMakeAssertions(rootBaseStore);

    const user = userEvent.setup();
    await user.click(screen.getByText('Retry'));

    expect(mockedSetupPlugin).toHaveBeenCalledTimes(2);
  });

  test('app successfully initialized', async () => {
    const rootBaseStore = new RootBaseStore();
    rootBaseStore.appLoading = false;
    rootBaseStore.initializationError = null;
    await createComponentAndMakeAssertions(rootBaseStore);
  });
});
