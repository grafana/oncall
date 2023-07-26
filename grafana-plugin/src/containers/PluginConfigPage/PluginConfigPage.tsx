import React, { FC, useCallback, useEffect, useState } from 'react';

import { Button, HorizontalGroup, Label, Legend, LinkButton, LoadingPlaceholder, VerticalGroup } from '@grafana/ui';
import { useLocation } from 'react-router-dom';
import { OnCallPluginConfigPageProps } from 'types';

import PluginState, { PluginStatusResponseBase } from 'state/plugin';
import { FALLBACK_LICENSE, GRAFANA_LICENSE_OSS } from 'utils/consts';

import ConfigurationForm from './parts/ConfigurationForm';
import RemoveCurrentConfigurationButton from './parts/RemoveCurrentConfigurationButton';
import StatusMessageBlock from './parts/StatusMessageBlock';

const PLUGIN_CONFIGURED_QUERY_PARAM = 'pluginConfigured';
const PLUGIN_CONFIGURED_QUERY_PARAM_TRUTHY_VALUE = 'true';

const PLUGIN_CONFIGURED_LICENSE_QUERY_PARAM = 'pluginConfiguredLicense';
const PLUGIN_CONFIGURED_VERSION_QUERY_PARAM = 'pluginConfiguredVersion';

/**
 * When everything is successfully configured, reload the page, and pass along a few query parameters
 * so that we avoid an infinite configuration-check/data-sync loop
 *
 * Don't refresh the page if the plugin is already enabled..
 */
export const reloadPageWithPluginConfiguredQueryParams = (
  { license, version }: PluginStatusResponseBase,
  pluginEnabled: boolean
): void => {
  if (!pluginEnabled) {
    window.location.href = `${window.location.href}?${PLUGIN_CONFIGURED_QUERY_PARAM}=${PLUGIN_CONFIGURED_QUERY_PARAM_TRUTHY_VALUE}&${PLUGIN_CONFIGURED_LICENSE_QUERY_PARAM}=${license}&${PLUGIN_CONFIGURED_VERSION_QUERY_PARAM}=${version}`;
  }
};

/**
 * remove the query params used to track state for a page reload after successful configuration, without triggering
 * a page reload
 * https://stackoverflow.com/a/19279428
 */
export const removePluginConfiguredQueryParams = (pluginIsEnabled: boolean): void => {
  if (history.pushState && pluginIsEnabled) {
    const newurl = `${window.location.protocol}//${window.location.host}${window.location.pathname}`;
    window.history.pushState({ path: newurl }, '', newurl);
  }
};

const PluginConfigPage: FC<OnCallPluginConfigPageProps> = ({
  plugin: {
    meta: { jsonData, enabled: pluginIsEnabled },
  },
}) => {
  const { search } = useLocation();
  const queryParams = new URLSearchParams(search);
  const pluginConfiguredQueryParam = queryParams.get(PLUGIN_CONFIGURED_QUERY_PARAM);
  const pluginConfiguredLicenseQueryParam = queryParams.get(PLUGIN_CONFIGURED_LICENSE_QUERY_PARAM);
  const pluginConfiguredVersionQueryParam = queryParams.get(PLUGIN_CONFIGURED_VERSION_QUERY_PARAM);

  const pluginConfiguredRedirect = pluginConfiguredQueryParam === PLUGIN_CONFIGURED_QUERY_PARAM_TRUTHY_VALUE;

  const [checkingIfPluginIsConnected, setCheckingIfPluginIsConnected] = useState<boolean>(!pluginConfiguredRedirect);
  const [pluginConnectionCheckError, setPluginConnectionCheckError] = useState<string>(null);
  const [pluginIsConnected, setPluginIsConnected] = useState<PluginStatusResponseBase>(
    pluginConfiguredRedirect
      ? {
          version: pluginConfiguredVersionQueryParam,
          license: pluginConfiguredLicenseQueryParam,
          recaptcha_site_key: 'abc',
          currently_undergoing_maintenance_message: 'false',
        }
      : null
  );

  const [updatingPluginStatus, setUpdatingPluginStatus] = useState<boolean>(false);
  const [updatingPluginStatusError, setUpdatingPluginStatusError] = useState<string>(null);

  const [resettingPlugin, setResettingPlugin] = useState<boolean>(false);
  const [pluginResetError, setPluginResetError] = useState<string>(null);

  const pluginMetaOnCallApiUrl = jsonData?.onCallApiUrl;
  const processEnvOnCallApiUrl = process.env.ONCALL_API_URL; // don't destructure this, will break how webpack supplies this
  const onCallApiUrl = pluginMetaOnCallApiUrl || processEnvOnCallApiUrl;
  const licenseType = pluginIsConnected?.license || FALLBACK_LICENSE;

  const resetQueryParams = useCallback(() => removePluginConfiguredQueryParams(pluginIsEnabled), [pluginIsEnabled]);

  const triggerUpdatePluginStatus = useCallback(async () => {
    resetMessages();
    setUpdatingPluginStatus(true);

    const pluginConnectionStatus = await PluginState.checkTokenAndIfPluginIsConnected(onCallApiUrl);

    if (typeof pluginConnectionStatus === 'string') {
      setUpdatingPluginStatusError(pluginConnectionStatus);
    } else {
      const { token_ok, ...versionLicenseInfo } = pluginConnectionStatus;
      setPluginIsConnected(versionLicenseInfo);
      reloadPageWithPluginConfiguredQueryParams(versionLicenseInfo, pluginIsEnabled);
    }

    setUpdatingPluginStatus(false);
  }, [onCallApiUrl, pluginIsEnabled]);

  useEffect(resetQueryParams, [resetQueryParams]);

  useEffect(() => {
    const configurePluginAndUpdatePluginStatus = async () => {
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
        const errorMsg = await PluginState.selfHostedInstallPlugin(processEnvOnCallApiUrl, true);
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
        const pluginConnectionResponse = await PluginState.updatePluginStatus(onCallApiUrl);

        if (typeof pluginConnectionResponse === 'string') {
          setPluginConnectionCheckError(pluginConnectionResponse);
        } else {
          triggerUpdatePluginStatus();
        }
      }
      setCheckingIfPluginIsConnected(false);
    };

    /**
     * don't check the plugin status (or trigger a data sync) if the user was just redirected after a successful
     * plugin setup
     */
    if (!pluginConfiguredRedirect) {
      configurePluginAndUpdatePluginStatus();
    }
  }, [pluginMetaOnCallApiUrl, processEnvOnCallApiUrl, onCallApiUrl, pluginConfiguredRedirect]);

  const resetMessages = useCallback(() => {
    setPluginResetError(null);
    setPluginConnectionCheckError(null);
    setPluginIsConnected(null);
    setUpdatingPluginStatusError(null);
  }, []);

  const resetState = useCallback(() => {
    resetMessages();
    resetQueryParams();
  }, [resetQueryParams]);

  const triggerPluginReset = useCallback(async () => {
    setResettingPlugin(true);
    resetState();

    try {
      await PluginState.resetPlugin();
      window.location.reload();
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

  const ReconfigurePluginButtons = () => (
    <HorizontalGroup>
      <Button variant="primary" onClick={triggerUpdatePluginStatus} size="md">
        Retry Sync
      </Button>
      {licenseType === GRAFANA_LICENSE_OSS ? <RemoveConfigButton /> : null}
    </HorizontalGroup>
  );

  let content: React.ReactNode;

  if (checkingIfPluginIsConnected) {
    content = <LoadingPlaceholder text="Validating your plugin connection..." />;
  } else if (updatingPluginStatus) {
    content = <LoadingPlaceholder text="Syncing data required for your plugin..." />;
  } else if (pluginConnectionCheckError || pluginResetError) {
    content = (
      <>
        <StatusMessageBlock text={pluginConnectionCheckError || pluginResetError} />
        <ReconfigurePluginButtons />
      </>
    );
  } else if (updatingPluginStatusError) {
    content = (
      <>
        <StatusMessageBlock text={updatingPluginStatusError} />
        <ReconfigurePluginButtons />
      </>
    );
  } else if (!pluginIsConnected) {
    content = (
      <ConfigurationForm onSuccessfulSetup={triggerUpdatePluginStatus} defaultOnCallApiUrl={processEnvOnCallApiUrl} />
    );
  } else {
    // plugin is fully connected and synced
    const pluginLink = (
      <LinkButton href={`/a/grafana-oncall-app/`} variant="primary">
        Open Grafana OnCall
      </LinkButton>
    );
    content =
      licenseType === GRAFANA_LICENSE_OSS ? (
        <HorizontalGroup>
          {pluginLink}
          <RemoveConfigButton />
        </HorizontalGroup>
      ) : (
        <VerticalGroup>
          <Label>This is a cloud managed configuration.</Label>
          {pluginLink}
        </VerticalGroup>
      );
  }

  return (
    <>
      <Legend>Configure Grafana OnCall</Legend>
      {pluginIsConnected ? (
        <>
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
