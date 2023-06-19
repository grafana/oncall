import { makeRequest as makeRequestOriginal, isNetworkError as isNetworkErrorOriginal } from 'network';

import PluginState, { InstallationVerb, PluginSyncStatusResponse, UpdateGrafanaPluginSettingsProps } from '.';

const makeRequest = makeRequestOriginal as jest.Mock<ReturnType<typeof makeRequestOriginal>>;
const isNetworkError = isNetworkErrorOriginal as unknown as jest.Mock<ReturnType<typeof isNetworkErrorOriginal>>;

jest.mock('network');

afterEach(() => {
  jest.resetAllMocks();
});

const ONCALL_BASE_URL = '/plugin';
const GRAFANA_PLUGIN_SETTINGS_URL = '/api/plugins/grafana-oncall-app/settings';

const generateMockNetworkError = (status: number, data = {}) => ({ response: { status, ...data } });

describe('PluginState.generateOnCallApiUrlConfiguredThroughEnvVarMsg', () => {
  test.each([true, false])(
    'it returns the proper error message - configured through env var: %s',
    (configuredThroughEnvVar) => {
      expect(PluginState.generateOnCallApiUrlConfiguredThroughEnvVarMsg(configuredThroughEnvVar)).toMatchSnapshot();
    }
  );
});

describe('PluginState.generateInvalidOnCallApiURLErrorMsg', () => {
  test.each([true, false])(
    'it returns the proper error message - configured through env var: %s',
    (configuredThroughEnvVar) => {
      expect(
        PluginState.generateInvalidOnCallApiURLErrorMsg('http://hello.com', configuredThroughEnvVar)
      ).toMatchSnapshot();
    }
  );
});

describe('PluginState.generateUnknownErrorMsg', () => {
  test.each([
    [true, 'install'],
    [true, 'sync'],
    [false, 'install'],
    [false, 'sync'],
  ])(
    'it returns the proper error message - configured through env var: %s',
    (configuredThroughEnvVar, verb: InstallationVerb) => {
      expect(PluginState.generateUnknownErrorMsg('http://hello.com', verb, configuredThroughEnvVar)).toMatchSnapshot();
    }
  );
});

describe('PluginState.getHumanReadableErrorFromOnCallError', () => {
  beforeEach(() => {
    console.warn = () => {};
  });

  test.each([502, 409])('it handles a non-400 network error properly - status code: %s', (status) => {
    isNetworkError.mockReturnValueOnce(true);

    expect(
      PluginState.getHumanReadableErrorFromOnCallError(
        generateMockNetworkError(status),
        'http://hello.com',
        'install',
        true
      )
    ).toMatchSnapshot();
  });

  test.each([true, false])(
    'it handles a 400 network error properly - has custom error message: %s',
    (hasCustomErrorMessage) => {
      isNetworkError.mockReturnValueOnce(true);

      const networkError = generateMockNetworkError(400) as any;
      if (hasCustomErrorMessage) {
        networkError.response.data = { error: 'ohhhh nooo an error' };
      }
      expect(
        PluginState.getHumanReadableErrorFromOnCallError(networkError, 'http://hello.com', 'install', true)
      ).toMatchSnapshot();
    }
  );

  test('it handles an unknown error properly', () => {
    isNetworkError.mockReturnValueOnce(false);

    expect(
      PluginState.getHumanReadableErrorFromOnCallError(new Error('asdfasdf'), 'http://hello.com', 'install', true)
    ).toMatchSnapshot();
  });
});

describe('PluginState.getHumanReadableErrorFromGrafanaProvisioningError', () => {
  beforeEach(() => {
    console.warn = () => {};
  });

  test.each([true, false])('it handles an error properly - network error: %s', (networkError) => {
    const onCallApiUrl = 'http://hello.com';
    const installationVerb = 'install';
    const onCallApiUrlIsConfiguredThroughEnvVar = true;
    const error = networkError ? generateMockNetworkError(400) : new Error('oh noooo');

    const mockGenerateInvalidOnCallApiURLErrorMsgResult = 'asdadslkjfkjlsd';
    const mockGenerateUnknownErrorMsgResult = 'asdadslkjfkjlsd';

    isNetworkError.mockReturnValueOnce(networkError);

    PluginState.generateInvalidOnCallApiURLErrorMsg = jest
      .fn()
      .mockReturnValueOnce(mockGenerateInvalidOnCallApiURLErrorMsgResult);
    PluginState.generateUnknownErrorMsg = jest.fn().mockReturnValueOnce(mockGenerateUnknownErrorMsgResult);

    const expectedErrorMsg = networkError
      ? mockGenerateInvalidOnCallApiURLErrorMsgResult
      : mockGenerateUnknownErrorMsgResult;

    expect(
      PluginState.getHumanReadableErrorFromGrafanaProvisioningError(
        error,
        onCallApiUrl,
        installationVerb,
        onCallApiUrlIsConfiguredThroughEnvVar
      )
    ).toEqual(expectedErrorMsg);

    if (networkError) {
      expect(PluginState.generateInvalidOnCallApiURLErrorMsg).toHaveBeenCalledTimes(1);
      expect(PluginState.generateInvalidOnCallApiURLErrorMsg).toHaveBeenCalledWith(
        onCallApiUrl,
        onCallApiUrlIsConfiguredThroughEnvVar
      );
    } else {
      expect(PluginState.generateUnknownErrorMsg).toHaveBeenCalledTimes(1);
      expect(PluginState.generateUnknownErrorMsg).toHaveBeenCalledWith(
        onCallApiUrl,
        installationVerb,
        onCallApiUrlIsConfiguredThroughEnvVar
      );
    }
  });
});

describe('PluginState.getGrafanaPluginSettings', () => {
  test('it calls the proper method', async () => {
    PluginState.grafanaBackend.get = jest.fn();

    await PluginState.getGrafanaPluginSettings();

    expect(PluginState.grafanaBackend.get).toHaveBeenCalledTimes(1);
    expect(PluginState.grafanaBackend.get).toHaveBeenCalledWith(GRAFANA_PLUGIN_SETTINGS_URL);
  });
});

describe('PluginState.updateGrafanaPluginSettings', () => {
  test.each([true, false])('it calls the proper method - enabled: %s', async (enabled) => {
    const data: UpdateGrafanaPluginSettingsProps = {
      jsonData: {
        onCallApiUrl: 'asdfasdf',
      },
      secureJsonData: {
        grafanaToken: 'kjdfkfdjkffd',
      },
    };

    PluginState.grafanaBackend.post = jest.fn();

    await PluginState.updateGrafanaPluginSettings(data, enabled);

    expect(PluginState.grafanaBackend.post).toHaveBeenCalledTimes(1);
    expect(PluginState.grafanaBackend.post).toHaveBeenCalledWith(GRAFANA_PLUGIN_SETTINGS_URL, {
      ...data,
      enabled,
      pinned: true,
    });
  });
});

describe('PluginState.createGrafanaToken', () => {
  test.each([true, false])('it calls the proper methods - existing key: %s', async (onCallKeyExists) => {
    const baseUrl = '/api/auth/keys';
    const onCallKeyId = 12345;
    const onCallKeyName = 'OnCall';
    const onCallKey = { name: onCallKeyName, id: onCallKeyId };
    const existingKeys = [{ name: 'foo', id: 9595 }];

    PluginState.grafanaBackend.get = jest
      .fn()
      .mockResolvedValueOnce(onCallKeyExists ? [...existingKeys, onCallKey] : existingKeys);
    PluginState.grafanaBackend.delete = jest.fn();
    PluginState.grafanaBackend.post = jest.fn();

    await PluginState.createGrafanaToken();

    expect(PluginState.grafanaBackend.get).toHaveBeenCalledTimes(1);
    expect(PluginState.grafanaBackend.get).toHaveBeenCalledWith(baseUrl);

    if (onCallKeyExists) {
      expect(PluginState.grafanaBackend.delete).toHaveBeenCalledTimes(1);
      expect(PluginState.grafanaBackend.delete).toHaveBeenCalledWith(`${baseUrl}/${onCallKeyId}`);
    } else {
      expect(PluginState.grafanaBackend.delete).not.toHaveBeenCalled();
    }

    expect(PluginState.grafanaBackend.post).toHaveBeenCalledTimes(1);
    expect(PluginState.grafanaBackend.post).toHaveBeenCalledWith(baseUrl, {
      name: onCallKeyName,
      role: 'Admin',
      secondsToLive: null,
    });
  });
});

describe('PluginState.getPluginSyncStatus', () => {
  test('it returns the plugin sync response', async () => {
    // mocks
    const mockedResp: PluginSyncStatusResponse = {
      license: 'asdasdf',
      version: 'asdasf',
      token_ok: true,
      recaptcha_site_key: 'asdasdf',
    };
    makeRequest.mockResolvedValueOnce(mockedResp);

    // test
    const response = await PluginState.getPluginSyncStatus();

    // assertions
    expect(response).toEqual(mockedResp);
    expect(makeRequest).toHaveBeenCalledTimes(1);
    expect(makeRequest).toHaveBeenCalledWith(`${ONCALL_BASE_URL}/sync`, { method: 'GET' });
  });
});

describe('PluginState.pollOnCallDataSyncStatus', () => {
  const onCallApiUrl = 'http://hello.com';
  const onCallApiUrlIsConfiguredThroughEnvVar = true;

  test('it returns an error message if the pollCount is greater than 10', async () => {
    // mocks
    const mockSyncResponse = { token_ok: false };

    PluginState.getPluginSyncStatus = jest.fn().mockResolvedValue(mockSyncResponse);
    PluginState.timeout = jest.fn();

    // test
    const response = await PluginState.pollOnCallDataSyncStatus(onCallApiUrl, onCallApiUrlIsConfiguredThroughEnvVar);

    // assertions
    expect(response).toMatchSnapshot();

    expect(PluginState.getPluginSyncStatus).toHaveBeenCalledTimes(11);
    expect(PluginState.getPluginSyncStatus).toHaveBeenCalledWith();

    expect(PluginState.timeout).toHaveBeenCalledTimes(11);
    expect(PluginState.timeout).toHaveBeenLastCalledWith(10);
  });

  test('it returns successfully if the getPluginSyncStatus response token_ok is true', async () => {
    // mocks
    const mockSyncResponse = { token_ok: true, foo: 'bar' };

    PluginState.getPluginSyncStatus = jest.fn().mockResolvedValueOnce(mockSyncResponse);

    // test
    const response = await PluginState.pollOnCallDataSyncStatus(onCallApiUrl, onCallApiUrlIsConfiguredThroughEnvVar);

    // assertions
    expect(response).toEqual(mockSyncResponse);

    expect(PluginState.getPluginSyncStatus).toHaveBeenCalledTimes(1);
    expect(PluginState.getPluginSyncStatus).toHaveBeenCalledWith();
  });

  test('it recursively calls itself if the getPluginSyncStatus response token_ok is not true', async () => {
    // mocks
    const mockSyncResponse = { token_ok: false };
    const mock_pollOnCallDataSyncStatusResponse = { foo: 'bar' };

    PluginState.getPluginSyncStatus = jest.fn().mockResolvedValueOnce(mockSyncResponse);
    PluginState.timeout = jest.fn();
    PluginState._pollOnCallDataSyncStatus = jest.fn().mockResolvedValueOnce(mock_pollOnCallDataSyncStatusResponse);

    // test
    const response = await PluginState.pollOnCallDataSyncStatus(onCallApiUrl, onCallApiUrlIsConfiguredThroughEnvVar, 8);

    // assertions
    expect(response).toEqual(mock_pollOnCallDataSyncStatusResponse);

    expect(PluginState.getPluginSyncStatus).toHaveBeenCalledTimes(1);
    expect(PluginState.getPluginSyncStatus).toHaveBeenCalledWith();

    expect(PluginState.timeout).toHaveBeenCalledTimes(1);
    expect(PluginState.timeout).toHaveBeenCalledWith(8);

    expect(PluginState._pollOnCallDataSyncStatus).toHaveBeenCalledTimes(1);
    expect(PluginState._pollOnCallDataSyncStatus).toHaveBeenCalledWith(
      onCallApiUrl,
      onCallApiUrlIsConfiguredThroughEnvVar,
      9
    );
  });

  test('it returns the result of getHumanReadableErrorFromOnCallError in the event of an error from getPluginSyncStatus', async () => {
    // mocks
    const mockError = { foo: 'bar' };
    const mockedHumanReadableError = 'kjdfkjfdjkfdkjfd';

    PluginState.getPluginSyncStatus = jest.fn().mockRejectedValueOnce(mockError);
    PluginState._pollOnCallDataSyncStatus = jest.fn();
    PluginState.getHumanReadableErrorFromOnCallError = jest.fn().mockReturnValueOnce(mockedHumanReadableError);

    // test
    const response = await PluginState.pollOnCallDataSyncStatus(onCallApiUrl, onCallApiUrlIsConfiguredThroughEnvVar);

    // assertions
    expect(response).toEqual(mockedHumanReadableError);

    expect(PluginState.getPluginSyncStatus).toHaveBeenCalledTimes(1);
    expect(PluginState.getPluginSyncStatus).toHaveBeenCalledWith();

    expect(PluginState.getHumanReadableErrorFromOnCallError).toHaveBeenCalledTimes(1);
    expect(PluginState.getHumanReadableErrorFromOnCallError).toHaveBeenCalledWith(
      mockError,
      onCallApiUrl,
      'sync',
      onCallApiUrlIsConfiguredThroughEnvVar
    );

    expect(PluginState._pollOnCallDataSyncStatus).not.toHaveBeenCalled();
  });

  test('it returns the result of getHumanReadableErrorFromOnCallError in the event of an error from a recursive call to pollOnCallDataSyncStatus', async () => {
    // mocks
    const mockSyncResponse = { token_ok: false };
    const mockError = { foo: 'bar' };
    const mockedHumanReadableError = 'kjdfkjfdjkfdkjfd';

    PluginState.getPluginSyncStatus = jest.fn().mockResolvedValueOnce(mockSyncResponse);
    PluginState._pollOnCallDataSyncStatus = jest.fn().mockRejectedValueOnce(mockError);
    PluginState.timeout = jest.fn();
    PluginState.getHumanReadableErrorFromOnCallError = jest.fn().mockReturnValueOnce(mockedHumanReadableError);

    // test
    const response = await PluginState.pollOnCallDataSyncStatus(onCallApiUrl, onCallApiUrlIsConfiguredThroughEnvVar, 5);

    // assertions
    expect(response).toEqual(mockedHumanReadableError);

    expect(PluginState.getPluginSyncStatus).toHaveBeenCalledTimes(1);
    expect(PluginState.getPluginSyncStatus).toHaveBeenCalledWith();

    expect(PluginState.timeout).toHaveBeenCalledTimes(1);
    expect(PluginState.timeout).toHaveBeenCalledWith(5);

    expect(PluginState._pollOnCallDataSyncStatus).toHaveBeenCalledTimes(1);
    expect(PluginState._pollOnCallDataSyncStatus).toHaveBeenCalledWith(
      onCallApiUrl,
      onCallApiUrlIsConfiguredThroughEnvVar,
      6
    );

    expect(PluginState.getHumanReadableErrorFromOnCallError).toHaveBeenCalledTimes(1);
    expect(PluginState.getHumanReadableErrorFromOnCallError).toHaveBeenCalledWith(
      mockError,
      onCallApiUrl,
      'sync',
      onCallApiUrlIsConfiguredThroughEnvVar
    );
  });
});

describe('PluginState.syncDataWithOnCall', () => {
  const onCallApiUrl = 'http://hello.com';
  const onCallApiUrlIsConfiguredThroughEnvVar = true;
  const requestUrl = `${ONCALL_BASE_URL}/sync`;
  const requestArgs = { method: 'POST' };

  test('it returns the error mesage if the start sync returns an error', async () => {
    // mocks
    const errorMsg = 'asdfasdf';

    makeRequest.mockResolvedValueOnce(errorMsg);
    PluginState.pollOnCallDataSyncStatus = jest.fn();

    // test
    const response = await PluginState.syncDataWithOnCall(onCallApiUrl, onCallApiUrlIsConfiguredThroughEnvVar);

    // assertions
    expect(response).toEqual(errorMsg);

    expect(makeRequest).toHaveBeenCalledTimes(1);
    expect(makeRequest).toHaveBeenCalledWith(requestUrl, requestArgs);

    expect(PluginState.pollOnCallDataSyncStatus).not.toHaveBeenCalled();
  });

  test('it calls pollOnCallDataSyncStatus if the start sync does not return an error', async () => {
    // mocks
    const mockedResponse = { foo: 'bar' };
    const mockedPollOnCallDataSyncStatusResponse = 'dfjkdfjdf';

    makeRequest.mockResolvedValueOnce(mockedResponse);
    PluginState.pollOnCallDataSyncStatus = jest.fn().mockResolvedValueOnce(mockedPollOnCallDataSyncStatusResponse);

    // test
    const response = await PluginState.syncDataWithOnCall(onCallApiUrl, onCallApiUrlIsConfiguredThroughEnvVar);

    // assertions
    expect(response).toEqual(mockedPollOnCallDataSyncStatusResponse);

    expect(makeRequest).toHaveBeenCalledTimes(1);
    expect(makeRequest).toHaveBeenCalledWith(requestUrl, requestArgs);

    expect(PluginState.pollOnCallDataSyncStatus).toHaveBeenCalledTimes(1);
    expect(PluginState.pollOnCallDataSyncStatus).toHaveBeenCalledWith(
      onCallApiUrl,
      onCallApiUrlIsConfiguredThroughEnvVar
    );
  });

  test('it calls getHumanReadableErrorFromOnCallError if an unknown error pops up', async () => {
    // mocks
    const mockedError = { foo: 'bar' };
    const mockedHumanReadableError = 'asdfjkdfjkdfjk';

    makeRequest.mockRejectedValueOnce(mockedError);
    PluginState.pollOnCallDataSyncStatus = jest.fn();
    PluginState.getHumanReadableErrorFromOnCallError = jest.fn().mockReturnValueOnce(mockedHumanReadableError);

    // test
    const response = await PluginState.syncDataWithOnCall(onCallApiUrl, onCallApiUrlIsConfiguredThroughEnvVar);

    // assertions
    expect(response).toEqual(mockedHumanReadableError);

    expect(makeRequest).toHaveBeenCalledTimes(1);
    expect(makeRequest).toHaveBeenCalledWith(requestUrl, requestArgs);

    expect(PluginState.getHumanReadableErrorFromOnCallError).toHaveBeenCalledTimes(1);
    expect(PluginState.getHumanReadableErrorFromOnCallError).toHaveBeenCalledWith(
      mockedError,
      onCallApiUrl,
      'sync',
      onCallApiUrlIsConfiguredThroughEnvVar
    );

    expect(PluginState.pollOnCallDataSyncStatus).not.toHaveBeenCalled();
  });
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
  test('it returns null if everything is successful', async () => {
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
    const response = await PluginState.selfHostedInstallPlugin(onCallApiUrl, false);

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

  test('it returns an error msg if it cannot update the provisioning settings the first time around', async () => {
    // mocks
    const onCallApiUrl = 'http://hello.com';
    const mockedError = new Error('ohhh nooo');
    const mockedHumanReadableError = 'asdflkajsdflkajsdf';

    PluginState.updateGrafanaPluginSettings = jest.fn().mockRejectedValueOnce(mockedError);
    PluginState.getHumanReadableErrorFromGrafanaProvisioningError = jest
      .fn()
      .mockReturnValueOnce(mockedHumanReadableError);

    // test
    const response = await PluginState.selfHostedInstallPlugin(onCallApiUrl, false);

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
      'install',
      false
    );
  });

  test('it returns an error msg if it fails when installing the plugin,', async () => {
    // mocks
    const onCallApiUrl = 'http://hello.com';
    const mockedError = new Error('ohhh nooo');
    const mockedHumanReadableError = 'asdflkajsdflkajsdf';

    PluginState.updateGrafanaPluginSettings = jest.fn();
    PluginState.installPlugin = jest.fn().mockRejectedValueOnce(mockedError);
    PluginState.getHumanReadableErrorFromOnCallError = jest.fn().mockReturnValueOnce(mockedHumanReadableError);

    // test
    const response = await PluginState.selfHostedInstallPlugin(onCallApiUrl, false);

    // assertions
    expect(response).toEqual(mockedHumanReadableError);

    expect(PluginState.installPlugin).toHaveBeenCalledTimes(1);
    expect(PluginState.installPlugin).toHaveBeenCalledWith(true);

    expect(PluginState.getHumanReadableErrorFromOnCallError).toHaveBeenCalledTimes(1);
    expect(PluginState.getHumanReadableErrorFromOnCallError).toHaveBeenCalledWith(
      mockedError,
      onCallApiUrl,
      'install',
      false
    );
  });

  test('it returns an error msg if it cannot update the provisioning settings the second time around', async () => {
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
    const response = await PluginState.selfHostedInstallPlugin(onCallApiUrl, false);

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
      'install',
      false
    );
  });
});

describe('PluginState.checkIfBackendIsInMaintenanceMode', () => {
  test('it returns the API response', async () => {
    // mocks
    const maintenanceModeMsg = 'asdfljkadsjlfkajsdf';
    const mockedResp = { currently_undergoing_maintenance_message: maintenanceModeMsg };
    const onCallApiUrl = 'http://hello.com';
    makeRequest.mockResolvedValueOnce(mockedResp);

    // test
    const response = await PluginState.checkIfBackendIsInMaintenanceMode(onCallApiUrl);

    // assertions
    expect(response).toEqual(maintenanceModeMsg);
    expect(makeRequest).toHaveBeenCalledTimes(1);
    expect(makeRequest).toHaveBeenCalledWith('/maintenance-mode-status', { method: 'GET' });
  });
});

describe('PluginState.checkIfPluginIsConnected', () => {
  test('it returns the API response', async () => {
    // mocks
    const mockedResp = { foo: 'bar' };
    const onCallApiUrl = 'http://hello.com';
    makeRequest.mockResolvedValueOnce(mockedResp);

    // test
    const response = await PluginState.checkIfPluginIsConnected(onCallApiUrl);

    // assertions
    expect(response).toEqual(mockedResp);

    expect(makeRequest).toHaveBeenCalledTimes(1);
    expect(makeRequest).toHaveBeenCalledWith(`${ONCALL_BASE_URL}/status`, { method: 'GET' });
  });

  test('it returns a human readable error in the event of an unsuccessful api call', async () => {
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
    expect(makeRequest).toHaveBeenCalledWith(`${ONCALL_BASE_URL}/status`, { method: 'GET' });

    expect(PluginState.getHumanReadableErrorFromOnCallError).toHaveBeenCalledTimes(1);
    expect(PluginState.getHumanReadableErrorFromOnCallError).toHaveBeenCalledWith(
      mockedError,
      onCallApiUrl,
      'install',
      false
    );
  });
});

describe('PluginState.resetPlugin', () => {
  test('it calls grafanaBackend.post with the proper settings', async () => {
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
