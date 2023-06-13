import React from 'react';

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';

import { CloudStore } from 'models/cloud/cloud';
import { UserStore } from 'models/user/user';
import { User } from 'models/user/user.types';
import { RootStore } from 'state';
import { useStore as useStoreOriginal } from 'state/useStore';

import MobileAppConnection from './MobileAppConnection';

jest.mock('plugin/GrafanaPluginRootPage.helpers', () => ({
  isTopNavbar: () => false,
}));

jest.mock('@grafana/runtime', () => ({
  config: {
    featureToggles: {
      topNav: false,
    },
  },
}));

jest.mock('utils/authorization', () => ({
  ...jest.requireActual('utils/authorization'),
  isUserActionAllowed: jest.fn().mockReturnValue(true),
}));

jest.mock('@grafana/runtime', () => ({
  getLocationSrv: jest.fn(),
}));

jest.mock('state/useStore');

const useStore = useStoreOriginal as jest.Mock<ReturnType<typeof useStoreOriginal>>;
const loadUserMock = jest.fn().mockReturnValue(undefined);

const mockUseStore = (rest?: any, connected = false, cloud_connected = true) => {
  const store = {
    userStore: {
      loadUser: loadUserMock,
      currentUser: {
        messaging_backends: {
          MOBILE_APP: { connected },
        },
      } as unknown as User,
      ...(rest ? rest : {}),
    } as unknown as UserStore,
    cloudStore: {
      getCloudConnectionStatus: jest.fn().mockReturnValue({ cloud_connection_status: cloud_connected }),
      cloudConnectionStatus: { cloud_connection_status: cloud_connected },
    } as unknown as CloudStore,
    hasFeature: jest.fn().mockReturnValue(true),
    isOpenSource: jest.fn().mockReturnValue(true),
  } as unknown as RootStore;

  useStore.mockReturnValue(store);

  return store;
};

const USER_PK = '8585';
const BACKEND = 'MOBILE_APP';

describe('MobileAppConnection', () => {
  beforeEach(() => {
    loadUserMock.mockClear();
  });

  test('it shows a loading message if it is currently fetching the QR code', async () => {
    const { userStore } = mockUseStore({
      sendBackendConfirmationCode: jest.fn().mockResolvedValueOnce('dfd'),
    });

    const component = render(<MobileAppConnection userPk={USER_PK} />);
    expect(component.container).toMatchSnapshot();

    await waitFor(() => {
      expect(userStore.sendBackendConfirmationCode).toHaveBeenCalledTimes(1);
      expect(userStore.sendBackendConfirmationCode).toHaveBeenCalledWith(USER_PK, BACKEND);
    });
  });

  test('it shows a message when the mobile app is already connected', async () => {
    const { userStore } = mockUseStore(
      {
        sendBackendConfirmationCode: jest.fn().mockResolvedValueOnce('dfd'),
      },
      true
    );

    const component = render(<MobileAppConnection userPk={USER_PK} />);
    expect(component.container).toMatchSnapshot();

    await waitFor(() => {
      expect(userStore.sendBackendConfirmationCode).toHaveBeenCalledTimes(0);
    });
  });

  test('it shows an error message if there was an error fetching the QR code', async () => {
    const { userStore } = mockUseStore({
      sendBackendConfirmationCode: jest.fn().mockRejectedValueOnce('dfd'),
    });

    const component = render(<MobileAppConnection userPk={USER_PK} />);
    await screen.findByText(/.*error fetching your QR code.*/);

    await waitFor(() => {
      expect(component.container).toMatchSnapshot();

      expect(userStore.sendBackendConfirmationCode).toHaveBeenCalledTimes(1);
      expect(userStore.sendBackendConfirmationCode).toHaveBeenCalledWith(USER_PK, BACKEND);
    });
  });

  test("it shows a QR code if the app isn't already connected", async () => {
    const { userStore } = mockUseStore({
      sendBackendConfirmationCode: jest.fn().mockResolvedValueOnce('dfd'),
    });

    const component = render(<MobileAppConnection userPk={USER_PK} />);
    expect(component.container).toMatchSnapshot();

    await waitFor(() => {
      expect(userStore.sendBackendConfirmationCode).toHaveBeenCalledTimes(1);
      expect(userStore.sendBackendConfirmationCode).toHaveBeenCalledWith(USER_PK, BACKEND);
    });
  });

  test('if we disconnect the app, it disconnects and fetches a new QR code', async () => {
    const { userStore } = mockUseStore(
      {
        sendBackendConfirmationCode: jest.fn().mockResolvedValueOnce('dfd'),
        unlinkBackend: jest.fn().mockResolvedValueOnce('asdfadsfafds'),
      },
      true
    );

    const component = render(<MobileAppConnection userPk={USER_PK} />);
    const button = await screen.findByRole('button');

    // click the disconnect button, which opens the modal
    await userEvent.click(button);
    // click the confirm button within the modal, which actually triggers the callback
    await userEvent.click(screen.getByText('Remove'));

    expect(component.container).toMatchSnapshot();

    await waitFor(() => {
      expect(userStore.sendBackendConfirmationCode).toHaveBeenCalledTimes(1);
      expect(userStore.sendBackendConfirmationCode).toHaveBeenCalledWith(USER_PK, BACKEND);

      expect(userStore.unlinkBackend).toHaveBeenCalledTimes(1);
      expect(userStore.unlinkBackend).toHaveBeenCalledWith(USER_PK, BACKEND);
    });
  });

  test('it shows a loading message if it is currently disconnecting', async () => {
    const { userStore } = mockUseStore(
      {
        sendBackendConfirmationCode: jest.fn().mockResolvedValueOnce('dfd'),
        unlinkBackend: jest.fn().mockResolvedValueOnce(new Promise((resolve) => setTimeout(resolve, 500))),
      },
      true
    );

    const component = render(<MobileAppConnection userPk={USER_PK} />);
    const button = await screen.findByRole('button');

    // click the disconnect button, which opens the modal
    await userEvent.click(button);
    // click the confirm button within the modal, which actually triggers the callback
    await userEvent.click(screen.getByText('Remove'));

    // wait for loading state
    await screen.findByText(/.*Loading.*/);

    expect(component.container).toMatchSnapshot();

    await waitFor(() => {
      expect(userStore.sendBackendConfirmationCode).toHaveBeenCalledTimes(1);
      expect(userStore.sendBackendConfirmationCode).toHaveBeenCalledWith(USER_PK, BACKEND);

      expect(userStore.unlinkBackend).toHaveBeenCalledTimes(1);
      expect(userStore.unlinkBackend).toHaveBeenCalledWith(USER_PK, BACKEND);
    });
  });

  test('it shows an error message if there was an error disconnecting the mobile app', async () => {
    const { userStore } = mockUseStore(
      {
        sendBackendConfirmationCode: jest.fn().mockResolvedValueOnce('dfd'),
        unlinkBackend: jest.fn().mockRejectedValueOnce('asdfadsfafds'),
      },
      true
    );

    const component = render(<MobileAppConnection userPk={USER_PK} />);
    const button = await screen.findByTestId('test__disconnect');

    // click the disconnect button, which opens the modal
    await userEvent.click(button);
    // click the confirm button within the modal, which actually triggers the callback
    await userEvent.click(screen.getByText('Remove'));

    await screen.findByText(/.*error disconnecting your mobile app.*/);

    expect(component.container).toMatchSnapshot();

    await waitFor(() => {
      expect(userStore.sendBackendConfirmationCode).toHaveBeenCalledTimes(0);

      expect(userStore.unlinkBackend).toHaveBeenCalledTimes(1);
      expect(userStore.unlinkBackend).toHaveBeenCalledWith(USER_PK, BACKEND);
    });
  });

  test('it polls loadUser on first render if not connected', async () => {
    mockUseStore(
      {
        sendBackendConfirmationCode: jest.fn().mockResolvedValueOnce('dfd'),
        unlinkBackend: jest.fn().mockRejectedValueOnce('asdfadsfafds'),
      },
      false
    );

    render(<MobileAppConnection userPk={USER_PK} />);

    await waitFor(
      () => {
        expect(loadUserMock).toHaveBeenCalled();
      },
      { timeout: 6000 }
    );
  });

  test('it polls loadUser after disconnect', async () => {
    mockUseStore(
      {
        sendBackendConfirmationCode: jest.fn().mockResolvedValueOnce('dff'),
        unlinkBackend: jest.fn().mockRejectedValueOnce('asdff'),
      },
      true
    );

    render(<MobileAppConnection userPk={USER_PK} />);
    const button = await screen.findByRole('button');

    loadUserMock.mockClear();

    await userEvent.click(button); // click the disconnect button, which opens the modal
    await userEvent.click(screen.getByText('Remove')); // click the confirm button within the modal, which actually triggers the callback

    await waitFor(
      () => {
        expect(loadUserMock).toHaveBeenCalled();
      },
      { timeout: 6000 }
    );
  });

  test('it shows a warning when cloud is not connected', async () => {
    mockUseStore({}, true, false);

    // Using MemoryRouter to avoid "Invariant failed: You should not use <Link> outside a <Router>"
    const component = render(
      <MemoryRouter>
        <MobileAppConnection userPk={USER_PK} />
      </MemoryRouter>
    );
    expect(component.container).toMatchSnapshot();
  });
});
