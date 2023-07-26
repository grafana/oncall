import React from 'react';

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useLocation as useLocationOriginal } from 'react-router-dom';
import { OnCallPluginConfigPageProps } from 'types';

import PluginState from 'state/plugin';

import PluginConfigPage, {
  reloadPageWithPluginConfiguredQueryParams,
  removePluginConfiguredQueryParams,
} from './PluginConfigPage';

jest.mock('../../../package.json', () => ({
  version: 'v1.2.3',
}));

jest.mock('react-router-dom', () => ({
  useLocation: jest.fn(() => ({
    search: '',
  })),
}));

const useLocation = useLocationOriginal as jest.Mock<ReturnType<typeof useLocationOriginal>>;

enum License {
  OSS = 'OpenSource',
  CLOUD = 'some-other-license',
}

const SELF_HOSTED_INSTALL_PLUGIN_ERROR_MESSAGE = 'ohhh nooo an error msg from self hosted install plugin';
const CHECK_IF_PLUGIN_IS_CONNECTED_ERROR_MESSAGE = 'ohhh nooo a plugin connection error';
const UPDATE_PLUGIN_STATUS_ERROR_MESSAGE = 'ohhh noooo a sync issue';
const PLUGIN_CONFIGURATION_FORM_DATA_ID = 'plugin-configuration-form';
const STATUS_MESSAGE_BLOCK_DATA_ID = 'status-message-block';

const MOCK_PROTOCOL = 'https:';
const MOCK_HOST = 'localhost:3000';
const MOCK_PATHNAME = '/dkjdfjkfd';
const MOCK_URL = `${MOCK_PROTOCOL}//${MOCK_HOST}${MOCK_PATHNAME}`;

/**
 * this is just a little hack to silence a warning that we'll get until we
 * upgrade to 16.9. See also: https://github.com/facebook/react/pull/14853
 * https://github.com/testing-library/react-testing-library#suppressing-unnecessary-warnings-on-react-dom-168
 */
const originalError = console.error;

beforeEach(() => {
  delete global.window.location;
  global.window ??= Object.create(window);
  global.window.location = {
    protocol: MOCK_PROTOCOL,
    host: MOCK_HOST,
    pathname: MOCK_PATHNAME,
    href: MOCK_URL,
  } as Location;
  global.window.history.pushState = jest.fn();

  console.error = (...args) => {
    if (/Warning.*not wrapped in act/.test(args[0])) {
      return;
    }
    originalError.call(console, ...args);
  };
});

afterEach(() => {
  jest.clearAllMocks();
  console.error = originalError;
});

const mockCheckTokenAndIfPluginIsConnected = (license: License = License.OSS) => {
  PluginState.checkTokenAndIfPluginIsConnected = jest.fn().mockResolvedValueOnce({
    token_ok: true,
    license,
    version: 'v1.2.3',
    allow_signup: true,
    currently_undergoing_maintenance_message: null,
    recaptcha_site_key: 'abc',
    is_installed: true,
    is_user_anonymous: false,
  });
};

const generateComponentProps = (
  onCallApiUrl: OnCallPluginConfigPageProps['plugin']['meta']['jsonData']['onCallApiUrl'] = null,
  enabled = false
): OnCallPluginConfigPageProps =>
  ({
    plugin: {
      meta: {
        jsonData: onCallApiUrl === null ? null : { onCallApiUrl },
        enabled,
      },
    },
  } as OnCallPluginConfigPageProps);

describe('reloadPageWithPluginConfiguredQueryParams', () => {
  test.each([true, false])(
    'it modifies the query params depending on whether or not the plugin is already enabled: enabled - %s',
    (pluginEnabled) => {
      // mocks
      const version = 'v1.2.3';
      const license = 'OpenSource';
      const recaptcha_site_key = 'abc';
      const currently_undergoing_maintenance_message = 'false';

      // test
      reloadPageWithPluginConfiguredQueryParams(
        { version, license, recaptcha_site_key, currently_undergoing_maintenance_message },
        pluginEnabled
      );

      // assertions
      expect(window.location.href).toEqual(
        pluginEnabled
          ? MOCK_URL
          : `${MOCK_URL}?pluginConfigured=true&pluginConfiguredLicense=${license}&pluginConfiguredVersion=${version}`
      );
    }
  );
});

describe('removePluginConfiguredQueryParams', () => {
  test('it removes all the query params if history.pushState is available, and plugin is enabled', () => {
    removePluginConfiguredQueryParams(true);
    expect(window.history.pushState).toBeCalledWith({ path: MOCK_URL }, '', MOCK_URL);
  });

  test('it does not remove all the query params if history.pushState is available, and plugin is disabled', () => {
    removePluginConfiguredQueryParams(false);
    expect(window.history.pushState).not.toHaveBeenCalled();
  });
});

describe('PluginConfigPage', () => {
  test('It removes the plugin configured query params if the plugin is enabled', async () => {
    // mocks
    const metaJsonDataOnCallApiUrl = 'onCallApiUrlFromMetaJsonData';
    PluginState.updatePluginStatus = jest.fn();
    mockCheckTokenAndIfPluginIsConnected();

    // test setup
    render(<PluginConfigPage {...generateComponentProps(metaJsonDataOnCallApiUrl, true)} />);
    await screen.findByTestId(STATUS_MESSAGE_BLOCK_DATA_ID);

    // assertions
    expect(window.history.pushState).toBeCalledWith({ path: MOCK_URL }, '', MOCK_URL);

    expect(PluginState.updatePluginStatus).toHaveBeenCalledTimes(1);
    expect(PluginState.updatePluginStatus).toHaveBeenCalledWith(metaJsonDataOnCallApiUrl);

    expect(PluginState.checkTokenAndIfPluginIsConnected).toHaveBeenCalledTimes(1);
    expect(PluginState.checkTokenAndIfPluginIsConnected).toHaveBeenCalledWith(metaJsonDataOnCallApiUrl);
  });

  test("It doesn't make any network calls if the plugin configured query params are provided", async () => {
    // mocks
    const metaJsonDataOnCallApiUrl = 'onCallApiUrlFromMetaJsonData';
    const version = 'v1.2.3';
    const license = 'OpenSource';

    useLocation.mockReturnValueOnce({
      search: `?pluginConfigured=true&pluginConfiguredLicense=${license}&pluginConfiguredVersion=${version}`,
    } as ReturnType<typeof useLocationOriginal>);

    PluginState.updatePluginStatus = jest.fn();
    mockCheckTokenAndIfPluginIsConnected();

    // test setup
    const component = render(<PluginConfigPage {...generateComponentProps(metaJsonDataOnCallApiUrl)} />);
    await screen.findByTestId(STATUS_MESSAGE_BLOCK_DATA_ID);

    // assertions
    expect(PluginState.updatePluginStatus).not.toHaveBeenCalled();
    expect(PluginState.checkTokenAndIfPluginIsConnected).not.toHaveBeenCalled();
    expect(component.container).toMatchSnapshot();
  });

  test("If onCallApiUrl is not set in the plugin's meta jsonData, or in process.env, updatePluginStatus is not called, and the configuration form is shown", async () => {
    // mocks
    delete process.env.ONCALL_API_URL;

    PluginState.updatePluginStatus = jest.fn();
    PluginState.checkTokenAndIfPluginIsConnected = jest.fn();

    // test setup
    const component = render(<PluginConfigPage {...generateComponentProps()} />);
    await screen.findByTestId(PLUGIN_CONFIGURATION_FORM_DATA_ID);

    // assertions
    expect(PluginState.updatePluginStatus).not.toHaveBeenCalled();
    expect(PluginState.checkTokenAndIfPluginIsConnected).not.toHaveBeenCalled();
    expect(component.container).toMatchSnapshot();
  });

  test("If onCallApiUrl is not set in the plugin's meta jsonData, and ONCALL_API_URL is passed in process.env, it calls selfHostedInstallPlugin", async () => {
    // mocks
    const processEnvOnCallApiUrl = 'onCallApiUrlFromProcessEnv';
    process.env.ONCALL_API_URL = processEnvOnCallApiUrl;

    PluginState.selfHostedInstallPlugin = jest.fn();
    mockCheckTokenAndIfPluginIsConnected();

    // test setup
    render(<PluginConfigPage {...generateComponentProps()} />);

    // assertions
    expect(PluginState.selfHostedInstallPlugin).toHaveBeenCalledTimes(1);
    expect(PluginState.selfHostedInstallPlugin).toHaveBeenCalledWith(processEnvOnCallApiUrl, true);
  });

  test("If onCallApiUrl is not set in the plugin's meta jsonData, and ONCALL_API_URL is passed in process.env, and there is an error calling selfHostedInstallPlugin, it sets an error message", async () => {
    // mocks
    const processEnvOnCallApiUrl = 'onCallApiUrlFromProcessEnv';
    process.env.ONCALL_API_URL = processEnvOnCallApiUrl;

    PluginState.selfHostedInstallPlugin = jest.fn().mockResolvedValueOnce(SELF_HOSTED_INSTALL_PLUGIN_ERROR_MESSAGE);

    // test setup
    const component = render(<PluginConfigPage {...generateComponentProps()} />);
    await screen.findByTestId(STATUS_MESSAGE_BLOCK_DATA_ID);

    // assertions
    expect(PluginState.selfHostedInstallPlugin).toHaveBeenCalledTimes(1);
    expect(PluginState.selfHostedInstallPlugin).toHaveBeenCalledWith(processEnvOnCallApiUrl, true);
    expect(component.container).toMatchSnapshot();
  });

  test('If onCallApiUrl is set, and updatePluginStatus returns an error, it sets an error message', async () => {
    // mocks
    const processEnvOnCallApiUrl = 'onCallApiUrlFromProcessEnv';
    const metaJsonDataOnCallApiUrl = 'onCallApiUrlFromMetaJsonData';

    process.env.ONCALL_API_URL = processEnvOnCallApiUrl;

    PluginState.updatePluginStatus = jest.fn().mockResolvedValueOnce(CHECK_IF_PLUGIN_IS_CONNECTED_ERROR_MESSAGE);

    // test setup
    const component = render(<PluginConfigPage {...generateComponentProps(metaJsonDataOnCallApiUrl)} />);
    await screen.findByTestId(STATUS_MESSAGE_BLOCK_DATA_ID);

    // assertions
    expect(PluginState.updatePluginStatus).toHaveBeenCalledTimes(1);
    expect(PluginState.updatePluginStatus).toHaveBeenCalledWith(metaJsonDataOnCallApiUrl);
    expect(component.container).toMatchSnapshot();
  });

  test('OnCallApiUrl is set, and checkTokenAndIfPluginIsConnected returns an error', async () => {
    // mocks
    const processEnvOnCallApiUrl = 'onCallApiUrlFromProcessEnv';
    const metaJsonDataOnCallApiUrl = 'onCallApiUrlFromMetaJsonData';

    process.env.ONCALL_API_URL = processEnvOnCallApiUrl;

    PluginState.updatePluginStatus = jest.fn().mockResolvedValueOnce(null);
    PluginState.checkTokenAndIfPluginIsConnected = jest.fn().mockResolvedValueOnce(UPDATE_PLUGIN_STATUS_ERROR_MESSAGE);

    // test setup
    const component = render(<PluginConfigPage {...generateComponentProps(metaJsonDataOnCallApiUrl)} />);
    await screen.findByTestId(STATUS_MESSAGE_BLOCK_DATA_ID);

    // assertions
    expect(PluginState.updatePluginStatus).toHaveBeenCalledTimes(1);
    expect(PluginState.updatePluginStatus).toHaveBeenCalledWith(metaJsonDataOnCallApiUrl);
    expect(component.container).toMatchSnapshot();
  });

  test.each([License.CLOUD, License.OSS])(
    'OnCallApiUrl is set, and checkTokenAndIfPluginIsConnected does not return an error. It displays properly the plugin connected items based on the license - License: %s',
    async (license) => {
      // mocks
      const processEnvOnCallApiUrl = 'onCallApiUrlFromProcessEnv';
      const metaJsonDataOnCallApiUrl = 'onCallApiUrlFromMetaJsonData';

      process.env.ONCALL_API_URL = processEnvOnCallApiUrl;

      PluginState.updatePluginStatus = jest.fn().mockResolvedValueOnce(null);
      mockCheckTokenAndIfPluginIsConnected(license);

      // test setup
      const component = render(<PluginConfigPage {...generateComponentProps(metaJsonDataOnCallApiUrl)} />);
      await screen.findByTestId(STATUS_MESSAGE_BLOCK_DATA_ID);

      // assertions
      expect(PluginState.updatePluginStatus).toHaveBeenCalledTimes(1);
      expect(PluginState.updatePluginStatus).toHaveBeenCalledWith(metaJsonDataOnCallApiUrl);
      expect(component.container).toMatchSnapshot();
    }
  );

  test.each([true, false])('Plugin reset: successful - %s', async (successful) => {
    // mocks
    const processEnvOnCallApiUrl = 'onCallApiUrlFromProcessEnv';
    const metaJsonDataOnCallApiUrl = 'onCallApiUrlFromMetaJsonData';

    process.env.ONCALL_API_URL = processEnvOnCallApiUrl;
    window.location.reload = jest.fn();

    PluginState.updatePluginStatus = jest.fn().mockResolvedValue(null);
    mockCheckTokenAndIfPluginIsConnected(License.OSS);

    if (successful) {
      PluginState.resetPlugin = jest.fn().mockResolvedValueOnce(null);
    } else {
      PluginState.resetPlugin = jest.fn().mockRejectedValueOnce('dfdf');
    }

    // test setup
    const component = render(<PluginConfigPage {...generateComponentProps(metaJsonDataOnCallApiUrl)} />);
    const button = await screen.findByRole('button');

    // click the reset button, which opens the modal
    await userEvent.click(button);
    // click the confirm button within the modal, which actually triggers the callback
    await userEvent.click(screen.getByText('Remove'));

    // assertions
    expect(PluginState.updatePluginStatus).toHaveBeenCalledTimes(1);
    expect(PluginState.updatePluginStatus).toHaveBeenCalledWith(metaJsonDataOnCallApiUrl);

    expect(PluginState.checkTokenAndIfPluginIsConnected).toHaveBeenCalledTimes(1);
    expect(PluginState.checkTokenAndIfPluginIsConnected).toHaveBeenCalledWith(metaJsonDataOnCallApiUrl);

    expect(PluginState.resetPlugin).toHaveBeenCalledTimes(1);
    expect(PluginState.resetPlugin).toHaveBeenCalledWith();

    expect(component.container).toMatchSnapshot();
  });
});
