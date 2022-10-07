import React from 'react';

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { OnCallPluginConfigPageProps } from 'types';

import PluginState from 'state/plugin';

import PluginConfigPage from './PluginConfigPage';

enum License {
  OSS = 'OpenSource',
  CLOUD = 'some-other-license',
}

const SELF_HOSTED_INSTALL_PLUGIN_ERROR_MESSAGE = 'ohhh nooo an error msg from self hosted install plugin';
const CHECK_IF_PLUGIN_IS_CONNECTED_ERROR_MESSAGE = 'ohhh nooo a plugin connection error';
const SNYC_DATA_WITH_ONCALL_ERROR_MESSAGE = 'ohhh noooo a sync issue';
const PLUGIN_CONFIGURATION_FORM_DATA_ID = 'plugin-configuration-form';
const STATUS_MESSAGE_BLOCK_DATA_ID = 'status-message-block';

const mockSyncDataWithOnCall = (license: License = License.OSS) => {
  PluginState.syncDataWithOnCall = jest.fn().mockResolvedValueOnce({
    token_ok: true,
    license,
    version: 'v1.2.3',
  });
};

const generateComponentProps = (
  onCallApiUrl: OnCallPluginConfigPageProps['plugin']['meta']['jsonData']['onCallApiUrl'] = null
): OnCallPluginConfigPageProps =>
  ({
    plugin: {
      meta: {
        jsonData: onCallApiUrl === null ? null : { onCallApiUrl },
      },
    },
  } as OnCallPluginConfigPageProps);

describe('PluginConfigPage', () => {
  afterEach(() => {
    jest.resetAllMocks();
  });

  test("If onCallApiUrl is not set in the plugin's meta jsonData, or in process.env, checkIfPluginIsConnected is not called, and the configuration form is shown", async () => {
    // mocks
    delete process.env.ONCALL_API_URL;

    PluginState.checkIfPluginIsConnected = jest.fn();
    PluginState.syncDataWithOnCall = jest.fn();

    // test setup
    const component = render(<PluginConfigPage {...generateComponentProps()} />);
    await waitFor(async () => screen.getByTestId(PLUGIN_CONFIGURATION_FORM_DATA_ID));

    // assertions
    expect(PluginState.checkIfPluginIsConnected).not.toHaveBeenCalled();
    expect(PluginState.syncDataWithOnCall).not.toHaveBeenCalled();
    expect(component.container).toMatchSnapshot();
  });

  test("If onCallApiUrl is not set in the plugin's meta jsonData, and ONCALL_API_URL is passed in process.env, it calls selfHostedInstallPlugin", async () => {
    // mocks
    const processEnvOnCallApiUrl = 'onCallApiUrlFromProcessEnv';
    process.env.ONCALL_API_URL = processEnvOnCallApiUrl;

    PluginState.selfHostedInstallPlugin = jest.fn();
    mockSyncDataWithOnCall();

    // test setup
    render(<PluginConfigPage {...generateComponentProps()} />);

    // assertions
    expect(PluginState.selfHostedInstallPlugin).toHaveBeenCalledTimes(1);
    expect(PluginState.selfHostedInstallPlugin).toHaveBeenCalledWith(processEnvOnCallApiUrl);
  });

  test("If onCallApiUrl is not set in the plugin's meta jsonData, and ONCALL_API_URL is passed in process.env, and there is an error calling selfHostedInstallPlugin, it sets an error message", async () => {
    // mocks
    const processEnvOnCallApiUrl = 'onCallApiUrlFromProcessEnv';
    process.env.ONCALL_API_URL = processEnvOnCallApiUrl;

    PluginState.selfHostedInstallPlugin = jest.fn().mockResolvedValueOnce(SELF_HOSTED_INSTALL_PLUGIN_ERROR_MESSAGE);

    // test setup
    const component = render(<PluginConfigPage {...generateComponentProps()} />);
    await waitFor(async () => screen.getByTestId(STATUS_MESSAGE_BLOCK_DATA_ID));

    // assertions
    expect(PluginState.selfHostedInstallPlugin).toHaveBeenCalledTimes(1);
    expect(PluginState.selfHostedInstallPlugin).toHaveBeenCalledWith(processEnvOnCallApiUrl);
    expect(component.container).toMatchSnapshot();
  });

  test('If onCallApiUrl is set, and checkIfPluginIsConnected returns an error, it sets an error message', async () => {
    // mocks
    const processEnvOnCallApiUrl = 'onCallApiUrlFromProcessEnv';
    const metaJsonDataOnCallApiUrl = 'onCallApiUrlFromMetaJsonData';

    process.env.ONCALL_API_URL = processEnvOnCallApiUrl;

    PluginState.checkIfPluginIsConnected = jest.fn().mockResolvedValueOnce(CHECK_IF_PLUGIN_IS_CONNECTED_ERROR_MESSAGE);

    // test setup
    const component = render(<PluginConfigPage {...generateComponentProps(metaJsonDataOnCallApiUrl)} />);
    await waitFor(async () => screen.getByTestId(STATUS_MESSAGE_BLOCK_DATA_ID));

    // assertions
    expect(PluginState.checkIfPluginIsConnected).toHaveBeenCalledTimes(1);
    expect(PluginState.checkIfPluginIsConnected).toHaveBeenCalledWith(metaJsonDataOnCallApiUrl);
    expect(component.container).toMatchSnapshot();
  });

  test('OnCallApiUrl is set, and syncDataWithOnCall returns an error', async () => {
    // mocks
    const processEnvOnCallApiUrl = 'onCallApiUrlFromProcessEnv';
    const metaJsonDataOnCallApiUrl = 'onCallApiUrlFromMetaJsonData';

    process.env.ONCALL_API_URL = processEnvOnCallApiUrl;

    PluginState.checkIfPluginIsConnected = jest.fn().mockResolvedValueOnce(null);
    PluginState.syncDataWithOnCall = jest.fn().mockResolvedValueOnce(SNYC_DATA_WITH_ONCALL_ERROR_MESSAGE);

    // test setup
    const component = render(<PluginConfigPage {...generateComponentProps(metaJsonDataOnCallApiUrl)} />);
    await waitFor(async () => screen.getByTestId(STATUS_MESSAGE_BLOCK_DATA_ID));

    // assertions
    expect(PluginState.checkIfPluginIsConnected).toHaveBeenCalledTimes(1);
    expect(PluginState.checkIfPluginIsConnected).toHaveBeenCalledWith(metaJsonDataOnCallApiUrl);
    expect(component.container).toMatchSnapshot();
  });

  test.each([License.CLOUD, License.OSS])(
    'OnCallApiUrl is set, and syncDataWithOnCall does not return an error. It displays properly the plugin connected items based on the license - License: %s',
    async (license) => {
      // mocks
      const processEnvOnCallApiUrl = 'onCallApiUrlFromProcessEnv';
      const metaJsonDataOnCallApiUrl = 'onCallApiUrlFromMetaJsonData';

      process.env.ONCALL_API_URL = processEnvOnCallApiUrl;

      PluginState.checkIfPluginIsConnected = jest.fn().mockResolvedValueOnce(null);
      mockSyncDataWithOnCall(license);

      // test setup
      const component = render(<PluginConfigPage {...generateComponentProps(metaJsonDataOnCallApiUrl)} />);
      await waitFor(async () => screen.getByTestId(STATUS_MESSAGE_BLOCK_DATA_ID));

      // assertions
      expect(PluginState.checkIfPluginIsConnected).toHaveBeenCalledTimes(1);
      expect(PluginState.checkIfPluginIsConnected).toHaveBeenCalledWith(metaJsonDataOnCallApiUrl);
      expect(component.container).toMatchSnapshot();
    }
  );

  test.each([true, false])('Plugin reset: successful - %s', async (successful) => {
    // mocks
    const processEnvOnCallApiUrl = 'onCallApiUrlFromProcessEnv';
    const metaJsonDataOnCallApiUrl = 'onCallApiUrlFromMetaJsonData';

    process.env.ONCALL_API_URL = processEnvOnCallApiUrl;

    PluginState.checkIfPluginIsConnected = jest.fn().mockResolvedValueOnce(null);
    mockSyncDataWithOnCall(License.OSS);

    if (successful) {
      PluginState.resetPlugin = jest.fn().mockResolvedValueOnce(null);
    } else {
      PluginState.resetPlugin = jest.fn().mockRejectedValueOnce('dfdf');
    }

    // test setup
    const component = render(<PluginConfigPage {...generateComponentProps(metaJsonDataOnCallApiUrl)} />);
    const user = userEvent.setup();

    let button: HTMLElement;
    await waitFor(async () => {
      button = screen.getByRole('button');
    });

    // click the reset button, which opens the modal
    await user.click(button);
    // click the confirm button within the modal, which actually triggers the callback
    await user.click(screen.getByText('Remove'));
    await waitFor(async () =>
      screen.getByTestId(successful ? PLUGIN_CONFIGURATION_FORM_DATA_ID : STATUS_MESSAGE_BLOCK_DATA_ID)
    );

    // assertions
    expect(PluginState.checkIfPluginIsConnected).toHaveBeenCalledTimes(1);
    expect(PluginState.checkIfPluginIsConnected).toHaveBeenCalledWith(metaJsonDataOnCallApiUrl);

    expect(PluginState.syncDataWithOnCall).toHaveBeenCalledTimes(1);
    expect(PluginState.syncDataWithOnCall).toHaveBeenCalledWith(metaJsonDataOnCallApiUrl);

    expect(PluginState.resetPlugin).toHaveBeenCalledTimes(1);
    expect(PluginState.resetPlugin).toHaveBeenCalledWith();

    expect(component.container).toMatchSnapshot();
  });
});
