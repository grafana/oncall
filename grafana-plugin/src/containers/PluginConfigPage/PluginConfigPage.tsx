import React, { useCallback, useEffect, useState } from 'react';

import { AppPluginMeta, PluginConfigPageProps } from '@grafana/data';
import { getBackendSrv } from '@grafana/runtime';
import {
  Button,
  Field,
  HorizontalGroup,
  VerticalGroup,
  Input,
  Label,
  Legend,
  LoadingPlaceholder,
  Icon,
  Alert,
  Modal,
} from '@grafana/ui';
import cn from 'classnames/bind';
import CopyToClipboard from 'react-copy-to-clipboard';
import { OnCallAppSettings } from 'types';

import Block from 'components/GBlock/Block';
import Text from 'components/Text/Text';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import logo from 'img/logo.svg';
import { makeRequest } from 'network';
import { createGrafanaToken, getPluginSyncStatus, startPluginSync, updateGrafanaToken } from 'state/plugin';
import { openNotification } from 'utils';
import { getItem, setItem } from 'utils/localStorage';

import styles from './PluginConfigPage.module.css';

const cx = cn.bind(styles);

interface Props extends PluginConfigPageProps<AppPluginMeta<OnCallAppSettings>> {}

export const PluginConfigPage = (props: Props) => {
  const { plugin } = props;
  const [onCallApiUrl, setOnCallApiUrl] = useState<string>(getItem('onCallApiUrl'));
  const [onCallInvitationToken, setOnCallInvitationToken] = useState<string>();
  const [grafanaUrl, setGrafanaUrl] = useState<string>(getItem('grafanaUrl'));
  const [pluginConfigLoading, setPluginConfigLoading] = useState<boolean>(true);
  const [pluginStatusOk, setPluginStatusOk] = useState<boolean>();
  const [pluginStatusMessage, setPluginStatusMessage] = useState<string>();
  const [isSelfHostedInstall, setIsSelfHostedInstall] = useState<boolean>(true);
  const [retrySync, setRetrySync] = useState<boolean>(false);

  const setupPlugin = useCallback(async () => {
    setItem('onCallApiUrl', onCallApiUrl);
    setItem('grafanaUrl', grafanaUrl);
    await getBackendSrv().post(`/api/plugins/grafana-oncall-app/settings`, {
      enabled: true,
      pinned: true,
      jsonData: {
        onCallApiUrl: onCallApiUrl,
        grafanaUrl: grafanaUrl,
      },
      secureJsonData: {
        onCallInvitationToken: onCallInvitationToken,
      },
    });

    const grafanaToken = await createGrafanaToken();
    await updateGrafanaToken(grafanaToken.key);

    let provisioningConfig;
    try {
      provisioningConfig = await makeRequest('/plugin/self-hosted/install', { method: 'POST' });
    } catch (e) {
      if (e.response.status === 502) {
        console.warn('Could not connect to OnCall: ' + onCallApiUrl);
      } else if (e.response.status === 403) {
        console.warn('Invitation token is invalid or expired.');
      } else {
        console.warn('Expected error: ' + e.response.status);
      }
    }

    if (provisioningConfig) {
      await getBackendSrv().post(`/api/plugins/grafana-oncall-app/settings`, {
        enabled: true,
        pinned: true,
        jsonData: {
          stackId: provisioningConfig.jsonData.stackId,
          orgId: provisioningConfig.jsonData.orgId,
          onCallApiUrl: onCallApiUrl,
          grafanaUrl: grafanaUrl,
          license: provisioningConfig.jsonData.license,
        },
        secureJsonData: {
          grafanaToken: grafanaToken.key,
          onCallApiToken: provisioningConfig.secureJsonData.onCallToken,
        },
      });
    }

    window.location.reload();
  }, [onCallApiUrl, onCallInvitationToken, grafanaUrl]);

  const resetPlugin = useCallback(async () => {
    await getBackendSrv().post(`/api/plugins/grafana-oncall-app/settings`, {
      enabled: false,
      pinned: true,
      jsonData: {
        stackId: null,
        orgId: null,
        onCallApiUrl: null,
        grafanaUrl: null,
      },
      secureJsonData: {
        grafanaToken: null,
        onCallApiToken: null,
      },
    });

    window.location.reload();
  }, []);

  const handleApiUrlChange = useCallback((e) => {
    setOnCallApiUrl(e.target.value);
  }, []);

  const handleInvitationTokenChange = useCallback((e) => {
    setOnCallInvitationToken(e.target.value);
  }, []);

  const handleGrafanaUrlChange = useCallback((e) => {
    setGrafanaUrl(e.target.value);
  }, []);

  const handleSyncException = useCallback((e) => {
    if (plugin.meta.jsonData?.onCallApiUrl) {
      let statusMessage = plugin.meta.jsonData.onCallApiUrl + '\n' + e + ', retry or check settings & re-initialize.';
      if (e.response.status == 404) {
        statusMessage += '\nIf Grafana OnCall was just installed, restart Grafana for OnCall routes to be available.';
      }
      setPluginStatusMessage(statusMessage);
      setRetrySync(true);
    } else {
      setPluginStatusMessage('OnCall has not been setup, configure & initialize below.');
    }
    setPluginStatusOk(false);
    setPluginConfigLoading(false);
  }, []);

  const finishSync = useCallback((get_sync_response) => {
    if (get_sync_response.token_ok) {
      const versionInfo =
        get_sync_response.version && get_sync_response.license
          ? ` (${get_sync_response.license}, ${get_sync_response.version})`
          : '';
      setPluginStatusMessage(
        `Connected to OnCall${versionInfo}\n - OnCall URL: ${plugin.meta.jsonData.onCallApiUrl}\n - Grafana URL: ${plugin.meta.jsonData.grafanaUrl}`
      );
      setIsSelfHostedInstall(plugin.meta.jsonData?.license === 'OpenSource');
      setPluginStatusOk(true);
    } else {
      setPluginStatusMessage(
        `OnCall failed to connect to this grafana via: ${plugin.meta.jsonData.grafanaUrl} check URL, network, and API key.`
      );
      setRetrySync(true);
    }
    setPluginConfigLoading(false);
  }, []);

  const startSync = useCallback(() => {
    setRetrySync(false);
    setPluginConfigLoading(true);
    startPluginSync()
      .then(() => {
        let counter = 0;
        const interval = setInterval(() => {
          counter++;

          getPluginSyncStatus()
            .then((get_sync_response) => {
              if (get_sync_response.hasOwnProperty('token_ok')) {
                clearInterval(interval);
                finishSync(get_sync_response);
              }
            })
            .catch((e) => {
              clearInterval(interval);
              handleSyncException(e);
            });

          if (counter >= 5) {
            clearInterval(interval);
            setPluginStatusMessage(
              `OnCall took too many tries to synchronize. Did you launch Celery workers? Background workers should perform synchronization, not web server.`
            );
            setRetrySync(true);
            setPluginStatusOk(false);
            setPluginConfigLoading(false);
          }
        }, 2000);
      })
      .catch(handleSyncException);
  }, []);

  useEffect(() => {
    startSync();
  }, []);

  return (
    <div>
      {pluginConfigLoading ? (
        <LoadingPlaceholder text="Loading..." />
      ) : pluginStatusOk || retrySync ? (
        <>
          <Legend>Configure Grafana OnCall</Legend>
          {pluginStatusOk && (
            <p>
              Plugin and the backend are connected! Check Grafana OnCall 👈👈👈{' '}
              <img alt="Grafana OnCall Logo" src={logo} width={18} />
            </p>
          )}
          <p>{'Plugin <-> backend connection status'}</p>
          <pre>
            <Text type="link">{pluginStatusMessage}</Text>
          </pre>

          <HorizontalGroup>
            {/* <p>{'Plugin <-> backend connection status'}</p>
              <pre>
                <Text type="link">{pluginStatusMessage}</Text>
              </pre> */}
            {retrySync && (
              <Button variant="primary" onClick={startSync} size="md">
                Retry
              </Button>
            )}
            {isSelfHostedInstall ? (
              <WithConfirm title="Are you sure to delete OnCall plugin configuration?">
                <Button variant="destructive" onClick={resetPlugin} size="md">
                  Remove current configuration
                </Button>
              </WithConfirm>
            ) : (
              <Label>This is a cloud managed configuration.</Label>
            )}{' '}
          </HorizontalGroup>
        </>
      ) : (
        <React.Fragment>
          <Legend>Configure Grafana OnCall</Legend>
          <p>This page will help you to connect OnCall backend and OnCall Grafana plugin 👋</p>

          <p>1. Launch backend</p>
          <VerticalGroup>
            <Text type="secondary">
              Run hobby, dev or production backend:{' '}
              <a href="https://github.com/grafana/oncall#getting-started">
                <Text type="link">getting started.</Text>
              </a>
            </Text>
          </VerticalGroup>
          <Block withBackground className={cx('info-block')}>
            <Text type="secondary">
              Need help?
              <br />- Talk to the OnCall team in the #grafana-oncall channel at{' '}
              <a href="https://slack.grafana.com/">
                <Text type="link">Slack</Text>
              </a>
              <br />- Ask questions at{' '}
              <a href="https://github.com/grafana/oncall/discussions/categories/q-a">
                <Text type="link">GitHub Discussions</Text>
              </a>{' '}
              or file bugs at{' '}
              <a href="https://github.com/grafana/oncall/issues">
                <Text type="link">GitHub Issues</Text>
              </a>
            </Text>
          </Block>

          <p>2. Conect the backend and the plugin </p>
          <p>{'Plugin <-> backend connection status:'}</p>
          <pre>
            <Text type="link">{pluginStatusMessage}</Text>
          </pre>
          <Field
            label="Invite token"
            description="Invite token is a 1-time secret used to make sure the backend is talking with the proper frontend. Find it at the end of the backend docker container logs.
Seek for such a line:  “Your invite token: <<LONG TOKEN>> , use it in the Grafana OnCall plugin.”"
          >
            <>
              <Input id="onCallInvitationToken" onChange={handleInvitationTokenChange} />
              <a href="https://github.com/grafana/oncall/blob/dev/DEVELOPER.md#frontend-setup">
                <Text size="small" type="link">
                  How to re-issue the invite token?
                </Text>
              </a>
            </>
          </Field>

          <Field
            label="OnCall backend URL"
            description={
              <Text>
                It should be reachable from Grafana. Possible options: <br />
                http://host.docker.internal:8080 (if you run backend in the docker locally)
                <br />
                http://localhost:8080 <br />
                ...
              </Text>
            }
          >
            <Input id="onCallApiUrl" onChange={handleApiUrlChange} defaultValue={onCallApiUrl} />
          </Field>
          <Field label="Grafana URL" description="URL of the current Grafana instance. ">
            <Input id="grafanaUrl" onChange={handleGrafanaUrlChange} defaultValue={grafanaUrl} />
          </Field>
          <Button
            variant="primary"
            onClick={setupPlugin}
            disabled={!onCallApiUrl || !onCallInvitationToken || !grafanaUrl}
            size="md"
          >
            Connect
          </Button>
        </React.Fragment>
      )}
    </div>
  );
};
