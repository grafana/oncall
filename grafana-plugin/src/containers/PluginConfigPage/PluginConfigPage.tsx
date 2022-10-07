import React, { FC, useCallback, useEffect, useState } from 'react';

import { Button, Label, Legend, LoadingPlaceholder } from '@grafana/ui';
import { OnCallPluginConfigPageProps } from 'types';

import logo from 'img/logo.svg';
import PluginState, { PluginStatusResponseBase } from 'state/plugin';
import { GRAFANA_LICENSE_OSS } from 'utils/consts';

import ConfigurationForm from './parts/ConfigurationForm';
import RemoveCurrentConfigurationButton from './parts/RemoveCurrentConfigurationButton';
import StatusMessageBlock from './parts/StatusMessageBlock';

const PluginConfigPage: FC<OnCallPluginConfigPageProps> = ({
  plugin: {
    meta: { jsonData },
  },
}) => {
  const [checkingIfPluginIsConnected, setCheckingIfPluginIsConnected] = useState<boolean>(true);
  const [pluginConnectionCheckError, setPluginConnectionCheckError] = useState<string>(null);
  const [pluginIsConnected, setPluginIsConnected] = useState<PluginStatusResponseBase>(null);

  const [syncingPlugin, setSyncingPlugin] = useState<boolean>(false);
  const [syncError, setSyncError] = useState<string>(null);

  const [resettingPlugin, setResettingPlugin] = useState<boolean>(false);
  const [pluginResetError, setPluginResetError] = useState<string>(null);

  const pluginMetaOnCallApiUrl = jsonData?.onCallApiUrl;
  const processEnvOnCallApiUrl = process.env.ONCALL_API_URL; // don't destructure this, will break how webpack supplies this
  const onCallApiUrl = pluginMetaOnCallApiUrl || processEnvOnCallApiUrl;
  const licenseType = pluginIsConnected?.license;

  const triggerDataSyncWithOnCall = useCallback(async () => {
    setSyncingPlugin(true);
    setSyncError(null);

    const syncDataResponse = await PluginState.syncDataWithOnCall(onCallApiUrl);

    if (typeof syncDataResponse === 'string') {
      setSyncError(syncDataResponse);
    } else {
      const { token_ok, ...versionLicenseInfo } = syncDataResponse;
      /**
       * TODO: refresh page, adding a query param, so that the OnCall logo shows up in the sidebar
       */
      setPluginIsConnected(versionLicenseInfo);
    }

    setSyncingPlugin(false);
  }, [onCallApiUrl]);

  useEffect(() => {
    (async () => {
      /**
       * If the plugin has never been configured, onCallApiUrl will be undefined in the plugin's jsonData
       * In that case, check to see if ONCALL_API_URL has been supplied as an env var.
       * Supplying the env var basically allows to skip the configuration form
       * (check webpack.config.js to see how this is set)
       */
      if (!pluginMetaOnCallApiUrl && processEnvOnCallApiUrl) {
        /**
         * onCallApiUrl is not yet saved in the grafana plugin settings, but has been supplied as an env var
         * lets auto-trigger a self-hosted plugin install w/ the onCallApiUrl passed in as an env var
         */
        const errorMsg = await PluginState.selfHostedInstallPlugin(processEnvOnCallApiUrl);
        if (errorMsg) {
          setPluginConnectionCheckError(errorMsg);
          setCheckingIfPluginIsConnected(false);
          return;
        }
      }

      /**
       * If the onCallApiUrl is not set in the plugin settings, and not supplied via an env var
       * there's no reason to check if the plugin is connected, we know it can't be
       */
      if (onCallApiUrl) {
        const pluginConnectionResponse = await PluginState.checkIfPluginIsConnected(onCallApiUrl);

        if (typeof pluginConnectionResponse === 'string') {
          setPluginConnectionCheckError(pluginConnectionResponse);
        } else {
          triggerDataSyncWithOnCall();
        }
      }
      setCheckingIfPluginIsConnected(false);
    })();
  }, [pluginMetaOnCallApiUrl, processEnvOnCallApiUrl, onCallApiUrl]);

  const resetState = useCallback(() => {
    setPluginResetError(null);
    setPluginConnectionCheckError(null);
    setPluginIsConnected(null);
    setSyncError(null);
  }, []);

  const triggerPluginReset = useCallback(async () => {
    setResettingPlugin(true);
    resetState();

    try {
      await PluginState.resetPlugin();
    } catch (e) {
      // this should rarely, if ever happen, but we should handle the case nevertheless
      setPluginResetError('There was an error resetting your plugin, try again.');
    }

    setResettingPlugin(false);
  }, [resetState]);

  const RemoveConfigButton = useCallback(
    () => <RemoveCurrentConfigurationButton disabled={resettingPlugin} onClick={triggerPluginReset} />,
    [resettingPlugin, triggerPluginReset]
  );

  let content: React.ReactNode;

  if (checkingIfPluginIsConnected) {
    content = <LoadingPlaceholder text="Validating your plugin connection..." />;
  } else if (syncingPlugin) {
    content = <LoadingPlaceholder text="Syncing data required for your plugin..." />;
  } else if (pluginConnectionCheckError || pluginResetError) {
    content = (
      <>
        <StatusMessageBlock text={pluginConnectionCheckError || pluginResetError} />
        <RemoveConfigButton />
      </>
    );
  } else if (syncError) {
    content = (
      <>
        <StatusMessageBlock text={syncError} />
        <Button variant="primary" onClick={triggerDataSyncWithOnCall} size="md">
          Retry Sync
        </Button>
      </>
    );
  } else if (!pluginIsConnected) {
    content = <ConfigurationForm onSuccessfulSetup={triggerDataSyncWithOnCall} />;
  } else {
    // plugin is fully connected and synced
    content =
      licenseType === GRAFANA_LICENSE_OSS ? (
        <RemoveConfigButton />
      ) : (
        <Label>This is a cloud managed configuration.</Label>
      );
  }

  return (
    <>
      <Legend>Configure Grafana OnCall</Legend>
      {pluginIsConnected ? (
        <>
          <p>
            Plugin is connected! Check Grafana OnCall 👈👈👈 <img alt="Grafana OnCall Logo" src={logo} width={18} />
          </p>
          <StatusMessageBlock
            text={`Connected to OnCall (${pluginIsConnected.version}, ${pluginIsConnected.license})`}
          />
        </>
      ) : (
        <p>This page will help you configure the OnCall plugin 👋</p>
      )}
      {content}
    </>
  );
};

export default PluginConfigPage;
