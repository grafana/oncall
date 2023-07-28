import { OrgRole } from '@grafana/data';
import { contextSrv } from 'grafana/app/core/core';
import { OnCallAppPluginMeta } from 'types';

import PluginState from 'state/plugin';
import { isUserActionAllowed as isUserActionAllowedOriginal } from 'utils/authorization';

import { RootBaseStore } from './';

jest.mock('state/plugin');
jest.mock('utils/authorization');
jest.mock('grafana/app/core/core', () => ({
  contextSrv: {
    user: {
      orgRole: null,
    },
  },
}));

const isUserActionAllowed = isUserActionAllowedOriginal as jest.Mock<ReturnType<typeof isUserActionAllowedOriginal>>;

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
    expect(rootBaseStore.initializationError).toEqual('🚫 Plugin has not been initialized');
  });

  test('when there is an issue checking the plugin connection, the error is properly handled', async () => {
    // mocks/setup
    const errorMsg = 'ohhh noooo error';
    const onCallApiUrl = 'http://asdfasdf.com';
    const rootBaseStore = new RootBaseStore();

    PluginState.updatePluginStatus = jest.fn().mockResolvedValueOnce(errorMsg);

    // test
    await rootBaseStore.setupPlugin(generatePluginData(onCallApiUrl));

    // assertions
    expect(PluginState.updatePluginStatus).toHaveBeenCalledTimes(1);
    expect(PluginState.updatePluginStatus).toHaveBeenCalledWith(onCallApiUrl);

    expect(rootBaseStore.initializationError).toEqual(errorMsg);
  });

  test('currently undergoing maintenance', async () => {
    // mocks/setup
    const onCallApiUrl = 'http://asdfasdf.com';
    const rootBaseStore = new RootBaseStore();
    const maintenanceMessage = 'mncvnmvcmnvkjdjkd';

    PluginState.updatePluginStatus = jest
      .fn()
      .mockResolvedValueOnce({ currently_undergoing_maintenance_message: maintenanceMessage });

    // test
    await rootBaseStore.setupPlugin(generatePluginData(onCallApiUrl));

    // assertions
    expect(PluginState.updatePluginStatus).toHaveBeenCalledTimes(1);
    expect(PluginState.updatePluginStatus).toHaveBeenCalledWith(onCallApiUrl);

    expect(rootBaseStore.initializationError).toEqual(`🚧 ${maintenanceMessage} 🚧`);
    expect(rootBaseStore.currentlyUndergoingMaintenance).toBe(true);
  });

  test('anonymous user', async () => {
    // mocks/setup
    const onCallApiUrl = 'http://asdfasdf.com';
    const rootBaseStore = new RootBaseStore();

    PluginState.updatePluginStatus = jest.fn().mockResolvedValueOnce({
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
    expect(PluginState.updatePluginStatus).toHaveBeenCalledTimes(1);
    expect(PluginState.updatePluginStatus).toHaveBeenCalledWith(onCallApiUrl);

    expect(rootBaseStore.initializationError).toEqual(
      '😞 Grafana OnCall is available for authorized users only, please sign in to proceed.'
    );
  });

  test('the plugin is not installed, and allow_signup is false', async () => {
    // mocks/setup
    const onCallApiUrl = 'http://asdfasdf.com';
    const rootBaseStore = new RootBaseStore();

    PluginState.updatePluginStatus = jest.fn().mockResolvedValueOnce({
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
    expect(PluginState.updatePluginStatus).toHaveBeenCalledTimes(1);
    expect(PluginState.updatePluginStatus).toHaveBeenCalledWith(onCallApiUrl);

    expect(PluginState.installPlugin).toHaveBeenCalledTimes(0);

    expect(rootBaseStore.initializationError).toEqual(
      '🚫 OnCall has temporarily disabled signup of new users. Please try again later.'
    );
  });

  test('plugin is not installed, user is not an Admin', async () => {
    // mocks/setup
    const onCallApiUrl = 'http://asdfasdf.com';
    const rootBaseStore = new RootBaseStore();

    contextSrv.user.orgRole = OrgRole.Viewer;
    contextSrv.accessControlEnabled = jest.fn().mockReturnValue(false);
    contextSrv.hasAccess = jest.fn().mockReturnValue(false);

    PluginState.updatePluginStatus = jest.fn().mockResolvedValueOnce({
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
    expect(PluginState.updatePluginStatus).toHaveBeenCalledTimes(1);
    expect(PluginState.updatePluginStatus).toHaveBeenCalledWith(onCallApiUrl);

    expect(PluginState.installPlugin).toHaveBeenCalledTimes(0);

    expect(rootBaseStore.initializationError).toEqual(
      '🚫 User with Admin permissions in your organization must sign on and setup OnCall before it can be used'
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

    contextSrv.user.orgRole = OrgRole.Admin;
    contextSrv.accessControlEnabled = jest.fn().mockResolvedValueOnce(false);
    contextSrv.hasAccess = jest.fn().mockReturnValue(true);

    PluginState.updatePluginStatus = jest.fn().mockResolvedValueOnce({
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
    expect(PluginState.updatePluginStatus).toHaveBeenCalledTimes(1);
    expect(PluginState.updatePluginStatus).toHaveBeenCalledWith(onCallApiUrl);

    expect(PluginState.installPlugin).toHaveBeenCalledTimes(1);
    expect(PluginState.installPlugin).toHaveBeenCalledWith();
  });

  test.each([
    { role: OrgRole.Admin, missing_permissions: [], expected_result: true },
    { role: OrgRole.Viewer, missing_permissions: [], expected_result: true },
    {
      role: OrgRole.Admin,
      missing_permissions: ['plugins:write', 'org.users:read', 'teams:read', 'apikeys:create', 'apikeys:delete'],
      expected_result: false,
    },
    {
      role: OrgRole.Viewer,
      missing_permissions: ['plugins:write', 'org.users:read', 'teams:read', 'apikeys:create', 'apikeys:delete'],
      expected_result: false,
    },
  ])('signup is allowed, accessControlEnabled, various roles and permissions', async (scenario) => {
    // mocks/setup
    const onCallApiUrl = 'http://asdfasdf.com';
    const rootBaseStore = new RootBaseStore();
    const mockedLoadCurrentUser = jest.fn();

    contextSrv.user.orgRole = scenario.role;
    contextSrv.accessControlEnabled = jest.fn().mockReturnValue(true);
    rootBaseStore.checkMissingSetupPermissions = jest.fn().mockImplementation(() => scenario.missing_permissions);

    PluginState.updatePluginStatus = jest.fn().mockResolvedValueOnce({
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
    expect(PluginState.updatePluginStatus).toHaveBeenCalledTimes(1);
    expect(PluginState.updatePluginStatus).toHaveBeenCalledWith(onCallApiUrl);

    if (scenario.expected_result) {
      expect(PluginState.installPlugin).toHaveBeenCalledTimes(1);
      expect(PluginState.installPlugin).toHaveBeenCalledWith();
    } else {
      expect(PluginState.installPlugin).toHaveBeenCalledTimes(0);

      expect(rootBaseStore.initializationError).toEqual(
        '🚫 User is missing permission(s) ' +
          scenario.missing_permissions.join(', ') +
          ' to setup OnCall before it can be used'
      );
    }
  });

  test('plugin is not installed, signup is allowed, the user is an admin, and plugin installation throws an error', async () => {
    // mocks/setup
    const onCallApiUrl = 'http://asdfasdf.com';
    const rootBaseStore = new RootBaseStore();
    const installPluginError = new Error('asdasdfasdfasf');
    const humanReadableErrorMsg = 'asdfasldkfjaksdjflk';

    contextSrv.user.orgRole = OrgRole.Admin;
    contextSrv.accessControlEnabled = jest.fn().mockReturnValue(false);
    contextSrv.hasAccess = jest.fn().mockReturnValue(true);

    PluginState.updatePluginStatus = jest.fn().mockResolvedValueOnce({
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
    expect(PluginState.updatePluginStatus).toHaveBeenCalledTimes(1);
    expect(PluginState.updatePluginStatus).toHaveBeenCalledWith(onCallApiUrl);

    expect(PluginState.installPlugin).toHaveBeenCalledTimes(1);
    expect(PluginState.installPlugin).toHaveBeenCalledWith();

    expect(PluginState.getHumanReadableErrorFromOnCallError).toHaveBeenCalledTimes(1);
    expect(PluginState.getHumanReadableErrorFromOnCallError).toHaveBeenCalledWith(
      installPluginError,
      onCallApiUrl,
      'install'
    );

    expect(rootBaseStore.initializationError).toEqual(humanReadableErrorMsg);
  });

  test('when the plugin is installed, a data sync is triggered', async () => {
    // mocks/setup
    const onCallApiUrl = 'http://asdfasdf.com';
    const rootBaseStore = new RootBaseStore();
    const mockedLoadCurrentUser = jest.fn();

    PluginState.updatePluginStatus = jest.fn().mockResolvedValueOnce({
      is_user_anonymous: false,
      is_installed: true,
      token_ok: true,
      allow_signup: true,
      version: 'asdfasdf',
      license: 'asdfasdf',
    });
    rootBaseStore.userStore.loadCurrentUser = mockedLoadCurrentUser;

    // test
    await rootBaseStore.setupPlugin(generatePluginData(onCallApiUrl));

    // assertions
    expect(PluginState.updatePluginStatus).toHaveBeenCalledTimes(1);
    expect(PluginState.updatePluginStatus).toHaveBeenCalledWith(onCallApiUrl);

    expect(mockedLoadCurrentUser).toHaveBeenCalledTimes(1);
    expect(mockedLoadCurrentUser).toHaveBeenCalledWith();

    expect(rootBaseStore.initializationError).toBeNull();
  });

  test('when the plugin is installed, and the data sync returns an error, it is properly handled', async () => {
    // mocks/setup
    const onCallApiUrl = 'http://asdfasdf.com';
    const rootBaseStore = new RootBaseStore();
    const mockedLoadCurrentUser = jest.fn();
    const updatePluginStatusError = 'asdasdfasdfasf';

    PluginState.updatePluginStatus = jest.fn().mockResolvedValueOnce({
      is_user_anonymous: false,
      is_installed: true,
      token_ok: true,
      allow_signup: true,
      version: 'asdfasdf',
      license: 'asdfasdf',
    });
    PluginState.updatePluginStatus = jest.fn().mockResolvedValueOnce(updatePluginStatusError);
    rootBaseStore.userStore.loadCurrentUser = mockedLoadCurrentUser;

    // test
    await rootBaseStore.setupPlugin(generatePluginData(onCallApiUrl));

    // assertions
    expect(PluginState.updatePluginStatus).toHaveBeenCalledTimes(1);
    expect(PluginState.updatePluginStatus).toHaveBeenCalledWith(onCallApiUrl);

    expect(rootBaseStore.initializationError).toEqual(updatePluginStatusError);
  });
});
