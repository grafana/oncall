import { OnCallAppPluginMeta } from 'types';

import PluginState from 'state/plugin';
import { UserActions, isUserActionAllowed as isUserActionAllowedOriginal } from 'utils/authorization';

import { RootBaseStore } from './';

jest.mock('state/plugin');
jest.mock('utils/authorization');

const isUserActionAllowed = isUserActionAllowedOriginal as jest.Mock<ReturnType<typeof isUserActionAllowedOriginal>>;

const PluginInstallAction = UserActions.PluginsInstall;

const generatePluginData = (
  onCallApiUrl: OnCallAppPluginMeta['jsonData']['onCallApiUrl'] = null
): OnCallAppPluginMeta =>
  ({
    jsonData: onCallApiUrl === null ? null : { onCallApiUrl },
  } as OnCallAppPluginMeta);

describe('rootBaseStore', () => {
  afterEach(() => {
    jest.resetAllMocks();
  });

  test("onCallApiUrl is not set in the plugin's meta jsonData", async () => {
    // mocks/setup
    const rootBaseStore = new RootBaseStore();

    // test
    await rootBaseStore.setupPlugin(generatePluginData());

    // assertions
    expect(rootBaseStore.appLoading).toBe(false);
    expect(rootBaseStore.initializationError).toEqual('🚫 Plugin has not been initialized');
  });

  test('when there is an issue checking the plugin connection, the error is properly handled', async () => {
    // mocks/setup
    const errorMsg = 'ohhh noooo error';
    const onCallApiUrl = 'http://asdfasdf.com';
    const rootBaseStore = new RootBaseStore();

    PluginState.checkIfPluginIsConnected = jest.fn().mockResolvedValueOnce(errorMsg);

    // test
    await rootBaseStore.setupPlugin(generatePluginData(onCallApiUrl));

    // assertions
    expect(PluginState.checkIfPluginIsConnected).toHaveBeenCalledTimes(1);
    expect(PluginState.checkIfPluginIsConnected).toHaveBeenCalledWith(onCallApiUrl);

    expect(rootBaseStore.appLoading).toBe(false);
    expect(rootBaseStore.initializationError).toEqual(errorMsg);
  });

  test('anonymous user', async () => {
    // mocks/setup
    const onCallApiUrl = 'http://asdfasdf.com';
    const rootBaseStore = new RootBaseStore();

    PluginState.checkIfPluginIsConnected = jest.fn().mockResolvedValueOnce({
      is_user_anonymous: true,
      is_installed: true,
      token_ok: true,
      allow_signup: true,
      version: 'asdfasdf',
      license: 'asdfasdf',
    });

    // test
    await rootBaseStore.setupPlugin(generatePluginData(onCallApiUrl));

    // assertions
    expect(PluginState.checkIfPluginIsConnected).toHaveBeenCalledTimes(1);
    expect(PluginState.checkIfPluginIsConnected).toHaveBeenCalledWith(onCallApiUrl);

    expect(rootBaseStore.appLoading).toBe(false);
    expect(rootBaseStore.initializationError).toEqual(
      '😞 Unfortunately Grafana OnCall is available for authorized users only, please sign in to proceed.'
    );
  });

  test('the plugin is not installed, and allow_signup is false', async () => {
    // mocks/setup
    const onCallApiUrl = 'http://asdfasdf.com';
    const rootBaseStore = new RootBaseStore();

    PluginState.checkIfPluginIsConnected = jest.fn().mockResolvedValueOnce({
      is_user_anonymous: false,
      is_installed: false,
      token_ok: true,
      allow_signup: false,
      version: 'asdfasdf',
      license: 'asdfasdf',
    });
    PluginState.installPlugin = jest.fn().mockResolvedValueOnce(null);

    // test
    await rootBaseStore.setupPlugin(generatePluginData(onCallApiUrl));

    // assertions
    expect(PluginState.checkIfPluginIsConnected).toHaveBeenCalledTimes(1);
    expect(PluginState.checkIfPluginIsConnected).toHaveBeenCalledWith(onCallApiUrl);

    expect(PluginState.installPlugin).toHaveBeenCalledTimes(0);

    expect(rootBaseStore.appLoading).toBe(false);
    expect(rootBaseStore.initializationError).toEqual(
      '🚫 OnCall has temporarily disabled signup of new users. Please try again later.'
    );
  });

  test('plugin is not installed, user is not an Admin', async () => {
    // mocks/setup
    const onCallApiUrl = 'http://asdfasdf.com';
    const rootBaseStore = new RootBaseStore();

    PluginState.checkIfPluginIsConnected = jest.fn().mockResolvedValueOnce({
      is_user_anonymous: false,
      is_installed: false,
      token_ok: true,
      allow_signup: true,
      version: 'asdfasdf',
      license: 'asdfasdf',
    });
    isUserActionAllowed.mockReturnValueOnce(false);
    PluginState.installPlugin = jest.fn().mockResolvedValueOnce(null);

    // test
    await rootBaseStore.setupPlugin(generatePluginData(onCallApiUrl));

    // assertions
    expect(PluginState.checkIfPluginIsConnected).toHaveBeenCalledTimes(1);
    expect(PluginState.checkIfPluginIsConnected).toHaveBeenCalledWith(onCallApiUrl);

    expect(isUserActionAllowed).toHaveBeenCalledTimes(1);
    expect(isUserActionAllowed).toHaveBeenCalledWith(PluginInstallAction);

    expect(PluginState.installPlugin).toHaveBeenCalledTimes(0);

    expect(rootBaseStore.appLoading).toBe(false);
    expect(rootBaseStore.initializationError).toEqual(
      '🚫 An Admin in your organization must sign on and setup OnCall before it can be used'
    );
  });

  test.each([
    { is_installed: false, token_ok: true },
    { is_installed: true, token_ok: false },
  ])('signup is allowed, user is an admin, plugin installation is triggered', async (scenario) => {
    // mocks/setup
    const onCallApiUrl = 'http://asdfasdf.com';
    const rootBaseStore = new RootBaseStore();
    const mockedLoadCurrentUser = jest.fn();

    PluginState.checkIfPluginIsConnected = jest.fn().mockResolvedValueOnce({
      ...scenario,
      is_user_anonymous: false,
      allow_signup: true,
      version: 'asdfasdf',
      license: 'asdfasdf',
    });
    isUserActionAllowed.mockReturnValueOnce(true);
    PluginState.installPlugin = jest.fn().mockResolvedValueOnce(null);
    rootBaseStore.userStore.loadCurrentUser = mockedLoadCurrentUser;

    // test
    await rootBaseStore.setupPlugin(generatePluginData(onCallApiUrl));

    // assertions
    expect(PluginState.checkIfPluginIsConnected).toHaveBeenCalledTimes(1);
    expect(PluginState.checkIfPluginIsConnected).toHaveBeenCalledWith(onCallApiUrl);

    expect(isUserActionAllowed).toHaveBeenCalledTimes(1);
    expect(isUserActionAllowed).toHaveBeenCalledWith(PluginInstallAction);

    expect(PluginState.installPlugin).toHaveBeenCalledTimes(1);
    expect(PluginState.installPlugin).toHaveBeenCalledWith();

    expect(mockedLoadCurrentUser).toHaveBeenCalledTimes(1);
    expect(mockedLoadCurrentUser).toHaveBeenCalledWith();

    expect(rootBaseStore.appLoading).toBe(false);
    expect(rootBaseStore.initializationError).toBeNull();
  });

  test('plugin is not installed, signup is allowed, the user is an admin, and plugin installation throws an error', async () => {
    // mocks/setup
    const onCallApiUrl = 'http://asdfasdf.com';
    const rootBaseStore = new RootBaseStore();
    const installPluginError = new Error('asdasdfasdfasf');
    const humanReadableErrorMsg = 'asdfasldkfjaksdjflk';

    PluginState.checkIfPluginIsConnected = jest.fn().mockResolvedValueOnce({
      is_user_anonymous: false,
      is_installed: false,
      token_ok: true,
      allow_signup: true,
      version: 'asdfasdf',
      license: 'asdfasdf',
    });
    isUserActionAllowed.mockReturnValueOnce(true);
    PluginState.installPlugin = jest.fn().mockRejectedValueOnce(installPluginError);
    PluginState.getHumanReadableErrorFromOnCallError = jest.fn().mockReturnValueOnce(humanReadableErrorMsg);

    // test
    await rootBaseStore.setupPlugin(generatePluginData(onCallApiUrl));

    // assertions
    expect(PluginState.checkIfPluginIsConnected).toHaveBeenCalledTimes(1);
    expect(PluginState.checkIfPluginIsConnected).toHaveBeenCalledWith(onCallApiUrl);

    expect(isUserActionAllowed).toHaveBeenCalledTimes(1);
    expect(isUserActionAllowed).toHaveBeenCalledWith(PluginInstallAction);

    expect(PluginState.installPlugin).toHaveBeenCalledTimes(1);
    expect(PluginState.installPlugin).toHaveBeenCalledWith();

    expect(PluginState.getHumanReadableErrorFromOnCallError).toHaveBeenCalledTimes(1);
    expect(PluginState.getHumanReadableErrorFromOnCallError).toHaveBeenCalledWith(
      installPluginError,
      onCallApiUrl,
      'install'
    );

    expect(rootBaseStore.appLoading).toBe(false);
    expect(rootBaseStore.initializationError).toEqual(humanReadableErrorMsg);
  });

  test('when the plugin is installed, a data sync is triggered', async () => {
    // mocks/setup
    const onCallApiUrl = 'http://asdfasdf.com';
    const rootBaseStore = new RootBaseStore();
    const mockedLoadCurrentUser = jest.fn();
    const version = 'asdfalkjslkjdf';
    const license = 'lkjdkjfdkjfdjkfd';

    PluginState.checkIfPluginIsConnected = jest.fn().mockResolvedValueOnce({
      is_user_anonymous: false,
      is_installed: true,
      token_ok: true,
      allow_signup: true,
      version: 'asdfasdf',
      license: 'asdfasdf',
    });
    PluginState.syncDataWithOnCall = jest.fn().mockResolvedValueOnce({ version, license, token_ok: true });
    rootBaseStore.userStore.loadCurrentUser = mockedLoadCurrentUser;

    // test
    await rootBaseStore.setupPlugin(generatePluginData(onCallApiUrl));

    // assertions
    expect(PluginState.checkIfPluginIsConnected).toHaveBeenCalledTimes(1);
    expect(PluginState.checkIfPluginIsConnected).toHaveBeenCalledWith(onCallApiUrl);

    expect(PluginState.syncDataWithOnCall).toHaveBeenCalledTimes(1);
    expect(PluginState.syncDataWithOnCall).toHaveBeenCalledWith(onCallApiUrl);

    expect(mockedLoadCurrentUser).toHaveBeenCalledTimes(1);
    expect(mockedLoadCurrentUser).toHaveBeenCalledWith();

    expect(rootBaseStore.appLoading).toBe(false);
    expect(rootBaseStore.initializationError).toBeNull();
  });

  test('when the plugin is installed, and the data sync returns an error, it is properly handled', async () => {
    // mocks/setup
    const onCallApiUrl = 'http://asdfasdf.com';
    const rootBaseStore = new RootBaseStore();
    const mockedLoadCurrentUser = jest.fn();
    const syncDataWithOnCallError = 'asdasdfasdfasf';

    PluginState.checkIfPluginIsConnected = jest.fn().mockResolvedValueOnce({
      is_user_anonymous: false,
      is_installed: true,
      token_ok: true,
      allow_signup: true,
      version: 'asdfasdf',
      license: 'asdfasdf',
    });
    PluginState.syncDataWithOnCall = jest.fn().mockResolvedValueOnce(syncDataWithOnCallError);
    rootBaseStore.userStore.loadCurrentUser = mockedLoadCurrentUser;

    // test
    await rootBaseStore.setupPlugin(generatePluginData(onCallApiUrl));

    // assertions
    expect(PluginState.checkIfPluginIsConnected).toHaveBeenCalledTimes(1);
    expect(PluginState.checkIfPluginIsConnected).toHaveBeenCalledWith(onCallApiUrl);

    expect(PluginState.syncDataWithOnCall).toHaveBeenCalledTimes(1);
    expect(PluginState.syncDataWithOnCall).toHaveBeenCalledWith(onCallApiUrl);

    expect(rootBaseStore.appLoading).toBe(false);
    expect(rootBaseStore.initializationError).toEqual(syncDataWithOnCallError);
  });
});
