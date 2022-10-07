import { makeRequest as makeRequestOriginal } from 'network';

import PluginState from './';

const makeRequest = makeRequestOriginal as jest.Mock<ReturnType<typeof makeRequestOriginal>>;

jest.mock('network');

afterEach(() => {
  jest.resetAllMocks();
});

describe('PluginState.installPlugin', () => {
  it.each([true, false])('returns the proper response - self hosted: %s', async (selfHosted) => {
    // mocks
    const mockedResponse = 'asdfasdf';
    const grafanaToken = 'asdfasdf';
    const mockedCreateGrafanaTokenResponse = { key: grafanaToken };

    makeRequest.mockResolvedValueOnce(mockedResponse);
    PluginState.createGrafanaToken = jest.fn().mockResolvedValueOnce(mockedCreateGrafanaTokenResponse);
    PluginState.updateGrafanaPluginSettings = jest.fn();

    // test
    const response = await PluginState.installPlugin(selfHosted);

    // assertions
    expect(response).toEqual({
      grafanaToken,
      onCallAPIResponse: mockedResponse,
    });

    expect(PluginState.createGrafanaToken).toBeCalledTimes(1);
    expect(PluginState.createGrafanaToken).toBeCalledWith();

    expect(PluginState.updateGrafanaPluginSettings).toBeCalledTimes(1);
    expect(PluginState.updateGrafanaPluginSettings).toBeCalledWith({
      secureJsonData: {
        grafanaToken,
      },
    });

    expect(makeRequest).toBeCalledTimes(1);
    expect(makeRequest).toBeCalledWith(`${PluginState.ONCALL_BASE_URL}/${selfHosted ? 'self-hosted/' : ''}install`, {
      method: 'POST',
    });
  });
});

describe('PluginState.selfHostedInstallPlugin', () => {
  it('returns null if everything is successful', async () => {
    // mocks
    const onCallApiUrl = 'http://hello.com';
    const installPluginResponse = {
      grafanaToken: 'asldkaljkasdfjklfdasklj',
      onCallAPIResponse: {
        stackId: 5,
        orgId: 5,
        license: 'asdfasdf',
        onCallToken: 'asdfasdf',
      },
    };
    const {
      grafanaToken,
      onCallAPIResponse: { onCallToken: onCallApiToken, ...jsonData },
    } = installPluginResponse;

    PluginState.updateGrafanaPluginSettings = jest.fn();
    PluginState.installPlugin = jest.fn().mockResolvedValueOnce(installPluginResponse);

    // test
    const response = await PluginState.selfHostedInstallPlugin(onCallApiUrl);

    // assertions
    expect(response).toBeNull();

    expect(PluginState.updateGrafanaPluginSettings).toHaveBeenNthCalledWith(1, {
      jsonData: {
        onCallApiUrl,
      },
    });

    expect(PluginState.installPlugin).toHaveBeenCalledTimes(1);
    expect(PluginState.installPlugin).toHaveBeenCalledWith(true);

    expect(PluginState.updateGrafanaPluginSettings).toHaveBeenNthCalledWith(2, {
      jsonData: {
        ...jsonData,
        onCallApiUrl,
      },
      secureJsonData: {
        grafanaToken,
        onCallApiToken,
      },
    });
  });

  it('returns an error msg if it cannot update the provisioning settings the first time around', async () => {
    // mocks
    const onCallApiUrl = 'http://hello.com';
    const mockedError = new Error('ohhh nooo');
    const mockedHumanReadableError = 'asdflkajsdflkajsdf';

    PluginState.updateGrafanaPluginSettings = jest.fn().mockRejectedValueOnce(mockedError);
    PluginState.getHumanReadableErrorFromGrafanaProvisioningError = jest
      .fn()
      .mockReturnValueOnce(mockedHumanReadableError);

    // test
    const response = await PluginState.selfHostedInstallPlugin(onCallApiUrl);

    // assertions
    expect(response).toEqual(mockedHumanReadableError);

    expect(PluginState.updateGrafanaPluginSettings).toHaveBeenCalledTimes(1);
    expect(PluginState.updateGrafanaPluginSettings).toHaveBeenCalledWith({
      jsonData: {
        onCallApiUrl,
      },
    });

    expect(PluginState.getHumanReadableErrorFromGrafanaProvisioningError).toHaveBeenCalledTimes(1);
    expect(PluginState.getHumanReadableErrorFromGrafanaProvisioningError).toHaveBeenCalledWith(
      mockedError,
      onCallApiUrl,
      'install'
    );
  });

  it('returns an error msg if it fails when installing the plugin,', async () => {
    // mocks
    const onCallApiUrl = 'http://hello.com';
    const mockedError = new Error('ohhh nooo');
    const mockedHumanReadableError = 'asdflkajsdflkajsdf';

    PluginState.updateGrafanaPluginSettings = jest.fn();
    PluginState.installPlugin = jest.fn().mockRejectedValueOnce(mockedError);
    PluginState.getHumanReadableErrorFromOnCallError = jest.fn().mockReturnValueOnce(mockedHumanReadableError);

    // test
    const response = await PluginState.selfHostedInstallPlugin(onCallApiUrl);

    // assertions
    expect(response).toEqual(mockedHumanReadableError);

    expect(PluginState.installPlugin).toHaveBeenCalledTimes(1);
    expect(PluginState.installPlugin).toHaveBeenCalledWith(true);

    expect(PluginState.getHumanReadableErrorFromOnCallError).toHaveBeenCalledTimes(1);
    expect(PluginState.getHumanReadableErrorFromOnCallError).toHaveBeenCalledWith(mockedError, onCallApiUrl, 'install');
  });

  it('returns an error msg if it cannot update the provisioning settings the second time around', async () => {
    // mocks
    const onCallApiUrl = 'http://hello.com';
    const mockedError = new Error('ohhh nooo');
    const mockedHumanReadableError = 'asdflkajsdflkajsdf';
    const installPluginResponse = {
      grafanaToken: 'asldkaljkasdfjklfdasklj',
      onCallAPIResponse: {
        stackId: 5,
        orgId: 5,
        license: 'asdfasdf',
        onCallToken: 'asdfasdf',
      },
    };
    const {
      grafanaToken,
      onCallAPIResponse: { onCallToken: onCallApiToken, ...jsonData },
    } = installPluginResponse;

    PluginState.updateGrafanaPluginSettings = jest.fn().mockResolvedValueOnce(null).mockRejectedValueOnce(mockedError);
    PluginState.installPlugin = jest.fn().mockResolvedValueOnce(installPluginResponse);
    PluginState.getHumanReadableErrorFromGrafanaProvisioningError = jest
      .fn()
      .mockReturnValueOnce(mockedHumanReadableError);

    // test
    const response = await PluginState.selfHostedInstallPlugin(onCallApiUrl);

    // assertions
    expect(response).toEqual(mockedHumanReadableError);

    expect(PluginState.updateGrafanaPluginSettings).toHaveBeenNthCalledWith(1, {
      jsonData: {
        onCallApiUrl,
      },
    });

    expect(PluginState.installPlugin).toHaveBeenCalledTimes(1);
    expect(PluginState.installPlugin).toHaveBeenCalledWith(true);

    expect(PluginState.updateGrafanaPluginSettings).toHaveBeenNthCalledWith(2, {
      jsonData: {
        ...jsonData,
        onCallApiUrl,
      },
      secureJsonData: {
        grafanaToken,
        onCallApiToken,
      },
    });

    expect(PluginState.getHumanReadableErrorFromGrafanaProvisioningError).toHaveBeenCalledTimes(1);
    expect(PluginState.getHumanReadableErrorFromGrafanaProvisioningError).toHaveBeenCalledWith(
      mockedError,
      onCallApiUrl,
      'install'
    );
  });
});

describe('PluginState.checkIfPluginIsConnected', () => {
  it('returns the response', async () => {
    // mocks
    const mockedResp = 'hello';
    const onCallApiUrl = 'http://hello.com';
    makeRequest.mockResolvedValueOnce(mockedResp);

    // test
    const response = await PluginState.checkIfPluginIsConnected(onCallApiUrl);

    // assertions
    expect(response).toEqual(mockedResp);
    expect(makeRequest).toHaveBeenCalledTimes(1);
    expect(makeRequest).toHaveBeenCalledWith(`/plugin/status`, { method: 'GET' });
  });

  it('returns a human readable error in the event of an unsuccessful api call', async () => {
    // mocks
    const mockedError = new Error('hello');
    const mockedHumanReadableError = 'asdflkajsdflkajsdf';
    const onCallApiUrl = 'http://hello.com';
    makeRequest.mockRejectedValueOnce(mockedError);

    PluginState.getHumanReadableErrorFromOnCallError = jest.fn().mockReturnValueOnce(mockedHumanReadableError);

    // test
    const response = await PluginState.checkIfPluginIsConnected(onCallApiUrl);

    // assertions
    expect(response).toEqual(mockedHumanReadableError);

    expect(makeRequest).toHaveBeenCalledTimes(1);
    expect(makeRequest).toHaveBeenCalledWith(`/plugin/status`, { method: 'GET' });

    expect(PluginState.getHumanReadableErrorFromOnCallError).toHaveBeenCalledTimes(1);
    expect(PluginState.getHumanReadableErrorFromOnCallError).toHaveBeenCalledWith(mockedError, onCallApiUrl, 'install');
  });
});

describe('PluginState.resetPlugin', () => {
  it('calls grafanaBackend.post with the proper settings', async () => {
    // mocks
    const mockedResponse = 'asdfasdf';
    PluginState.updateGrafanaPluginSettings = jest.fn().mockResolvedValueOnce(mockedResponse);

    // test
    const response = await PluginState.resetPlugin();

    // assertions
    expect(response).toEqual(mockedResponse);
    expect(PluginState.updateGrafanaPluginSettings).toHaveBeenCalledTimes(1);
    expect(PluginState.updateGrafanaPluginSettings).toHaveBeenCalledWith(
      {
        jsonData: {
          stackId: null,
          orgId: null,
          onCallApiUrl: null,
          license: null,
        },
        secureJsonData: {
          grafanaToken: null,
          onCallApiToken: null,
        },
      },
      false
    );
  });
});
