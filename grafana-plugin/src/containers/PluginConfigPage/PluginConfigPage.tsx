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
} from '@grafana/ui';
import cn from 'classnames/bind';
import { OnCallAppSettings } from 'types';

import Block from 'components/GBlock/Block';
import Text from 'components/Text/Text';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import logo from 'img/logo.svg';
import { makeRequest } from 'network';
import { createGrafanaToken, getPluginSyncStatus, startPluginSync, updateGrafanaToken } from 'state/plugin';
import { GRAFANA_LICENSE_OSS } from 'utils/consts';
import { getItem, setItem } from 'utils/localStorage';

import { constructSyncErrorMessage, constructErrorActionMessage } from './helpers';

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

  const INVALID_INVITE_TOKEN_ERROR_MSG = `It seems like your invite token may be invalid. ${constructErrorActionMessage('generating a new invite token')}`;

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
    const buildErrMsg = (msg: string): string =>
      constructSyncErrorMessage(msg, plugin.meta.jsonData?.onCallApiUrl);

    if (plugin.meta.jsonData?.onCallApiUrl) {
      const { status: statusCode  } = e.response;

      let statusMessage: string;

      if (statusCode == 403) {
        statusMessage = buildErrMsg(INVALID_INVITE_TOKEN_ERROR_MSG);
      } else if (statusCode === 404) {
        statusMessage = buildErrMsg('If Grafana OnCall was just installed, restart Grafana for OnCall routes to be available.');
      } else if (statusCode === 502) {
        statusMessage = buildErrMsg(`Unable to communicate with either the Grafana API, or Grafana OnCall engine API. ${constructErrorActionMessage('verify that the API URLs that you entered are correct')}`);
      } else {
        statusMessage = buildErrMsg(`An unknown error occured. ${constructErrorActionMessage()}. If the error still occurs please reach out to support.`)
      }
      setPluginStatusMessage(statusMessage);
      setRetrySync(true);
    } else {
      setPluginStatusMessage(buildErrMsg('OnCall has not been setup, configure & initialize below.'));
    }
    setPluginStatusOk(false);
    setPluginConfigLoading(false);
  }, []);

  const finishSync = useCallback((getSyncResponse) => {
    if (getSyncResponse.token_ok) {
      const versionInfo =
        getSyncResponse.version && getSyncResponse.license
          ? ` (${getSyncResponse.license}, ${getSyncResponse.version})`
          : '';

      let pluginStatusMessage = `Connected to OnCall${versionInfo}\n - OnCall URL: ${plugin.meta.jsonData.onCallApiUrl}\n`
      if (plugin.meta.jsonData.grafanaUrl) {
        pluginStatusMessage = `${pluginStatusMessage} - Grafana URL: ${plugin.meta.jsonData.grafanaUrl}`
      }

      setPluginStatusMessage(pluginStatusMessage)
      setIsSelfHostedInstall(plugin.meta.jsonData?.license === GRAFANA_LICENSE_OSS);
      setPluginStatusOk(true);
    } else {
      setPluginStatusMessage(constructSyncErrorMessage(INVALID_INVITE_TOKEN_ERROR_MSG,
        plugin.meta.jsonData.grafanaUrl));
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
            <Text>{pluginStatusMessage}</Text>
          </pre>

          <HorizontalGroup>
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
              <a href="https://github.com/grafana/oncall#getting-started" target="_blank" rel="noreferrer">
                <Text type="link">getting started.</Text>
              </a>
            </Text>
          </VerticalGroup>
          <Block withBackground className={cx('info-block')}>
            <Text type="secondary">
              Need help?
              <br />- Talk to the OnCall team in the #grafana-oncall channel at{' '}
              <a href="https://slack.grafana.com/" target="_blank" rel="noreferrer">
                <Text type="link">Slack</Text>
              </a>
              <br />- Ask questions at{' '}
              <a href="https://github.com/grafana/oncall/discussions/categories/q-a" target="_blank" rel="noreferrer">
                <Text type="link">GitHub Discussions</Text>
              </a>{' '}
              or file bugs at{' '}
              <a href="https://github.com/grafana/oncall/issues" target="_blank" rel="noreferrer">
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
              <a href="https://github.com/grafana/oncall/blob/dev/DEVELOPER.md#frontend-setup" target="_blank" rel="noreferrer">
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
