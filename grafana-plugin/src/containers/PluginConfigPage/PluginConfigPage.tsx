import React, { useEffect, useState } from 'react';

import { css } from '@emotion/css';
import { GrafanaTheme2, PluginConfigPageProps, PluginMeta } from '@grafana/data';
import { Alert, Field, Input, LoadingPlaceholder, useStyles2, Stack } from '@grafana/ui';
import { OnCallPluginMetaJSONData } from 'app-types';
import {
  DEFAULT_PAGE,
  DOCS_ONCALL_OSS_INSTALL,
  DOCS_SERVICE_ACCOUNTS,
  IS_CURRENT_ENV_CLOUD,
  PLUGIN_CONFIG,
  PLUGIN_ROOT,
  REQUEST_HELP_URL,
} from 'helpers/consts';
import { getIsExternalServiceAccountFeatureAvailable } from 'helpers/helpers';
import { useOnMount } from 'helpers/hooks';
import { validateURL } from 'helpers/string';
import { observer } from 'mobx-react';
import { Controller, useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom-v5-compat';

import { Button } from 'components/Button/Button';
import { CollapsibleTreeView } from 'components/CollapsibleTreeView/CollapsibleTreeView';
import { RenderConditionally } from 'components/RenderConditionally/RenderConditionally';
import { Text } from 'components/Text/Text';
import { ActionKey } from 'models/loader/action-keys';
import { rootStore } from 'state/rootStore';

type PluginConfigFormValues = {
  onCallApiUrl: string;
};

export const PluginConfigPage = observer((props: PluginConfigPageProps<PluginMeta<OnCallPluginMetaJSONData>>) => {
  const {
    pluginStore: { verifyPluginConnection, refreshAppliedOnCallApiUrl },
  } = rootStore;

  useOnMount(() => {
    refreshAppliedOnCallApiUrl();
    verifyPluginConnection();
  });

  return (
    <Stack direction="column">
      <Text.Title
        level={3}
        className={css`
          margin-bottom: 12px;
        `}
      >
        Configure Grafana OnCall
      </Text.Title>
      {IS_CURRENT_ENV_CLOUD ? <CloudPluginConfigPage {...props} /> : <OSSPluginConfigPage {...props} />}
    </Stack>
  );
});

const CloudPluginConfigPage = observer(
  ({ plugin: { meta } }: PluginConfigPageProps<PluginMeta<OnCallPluginMetaJSONData>>) => {
    const {
      pluginStore: { isPluginConnected },
    } = rootStore;
    const styles = useStyles2(getStyles);

    return (
      <Stack direction="column">
        <Text type="secondary" className={styles.secondaryTitle}>
          This is a cloud-managed configuration.
        </Text>
        <RenderConditionally shouldRender={meta.enabled} render={() => <PluginConfigAlert />} />
        <RenderConditionally
          shouldRender={!isPluginConnected}
          render={() => <Button onClick={() => window.open(REQUEST_HELP_URL, '_blank')}>Request help</Button>}
        />
      </Stack>
    );
  }
);

const OSSPluginConfigPage = observer(
  ({ plugin: { meta } }: PluginConfigPageProps<PluginMeta<OnCallPluginMetaJSONData>>) => {
    const {
      pluginStore: {
        updatePluginSettingsAndReinitializePlugin,
        connectionStatus,
        recreateServiceAccountAndRecheckPluginStatus,
        isPluginConnected,
        appliedOnCallApiUrl,
        enablePlugin,
      },
      loaderStore,
    } = rootStore;
    const [hasBeenReconnected, setHasBeenReconnected] = useState(false);
    const navigate = useNavigate();
    const styles = useStyles2(getStyles);
    const { handleSubmit, control, formState } = useForm<PluginConfigFormValues>({
      mode: 'onChange',
      values: { onCallApiUrl: appliedOnCallApiUrl },
    });
    const isReinitializating = loaderStore.isLoading(ActionKey.PLUGIN_UPDATE_SETTINGS_AND_REINITIALIZE);
    const isRecreatingServiceAccount = loaderStore.isLoading(ActionKey.PLUGIN_RECREATE_SERVICE_ACCOUNT);

    const isSubmitButtonDisabled = !formState.isValid || !meta.enabled || isReinitializating;

    const showAlert = meta.enabled && (!isPluginConnected || hasBeenReconnected);

    const onSubmit = async (values: PluginConfigFormValues) => {
      await updatePluginSettingsAndReinitializePlugin({
        currentJsonData: meta.jsonData,
        newJsonData: { onCallApiUrl: values.onCallApiUrl },
      });
      setHasBeenReconnected(true);
    };

    const getCheckOrTextIcon = (isOk: boolean) => (isOk ? { customIcon: 'check' as const } : { isTextIcon: true });

    const enablePluginExpandedView = () => (
      <>
        <Text strong>Enable OnCall plugin</Text>
        <Text type="secondary" className={styles.secondaryTitle}>
          Make sure that OnCall plugin has been enabled.
        </Text>
        <RenderConditionally
          shouldRender={!meta.enabled}
          render={() => (
            <Button variant="secondary" onClick={enablePlugin}>
              Enable
            </Button>
          )}
        />
      </>
    );

    const serviceAccountTokenExpandedView = () => (
      <>
        <Text strong>Service account user allows to connect OnCall plugin to Grafana. </Text>
        <Text type="secondary" className={styles.secondaryTitle}>
          Make sure that OnCall plugin has been enabled.{' '}
          <a href={DOCS_SERVICE_ACCOUNTS} target="_blank" rel="noreferrer">
            <Text type="link">Read more</Text>
          </a>
        </Text>
        <Stack>
          <Button
            variant="secondary"
            onClick={recreateServiceAccountAndRecheckPluginStatus}
            data-testid="recreate-service-account"
          >
            Re-create
          </Button>
          <RenderConditionally
            shouldRender={isRecreatingServiceAccount}
            render={() => <LoadingPlaceholder text="" className={styles.spinner} />}
          />
        </Stack>
      </>
    );

    const onCallApiUrlExpandedView = () => (
      <>
        <Text strong>Let us know the backend URL for your OnCall API</Text>
        <Text type="secondary" className={styles.secondaryTitle}>
          OnCall backend must be reachable from your Grafana Installation. <br />
          You can run hobby, dev or production backend. See{' '}
          <a href={DOCS_ONCALL_OSS_INSTALL} target="_blank" rel="noreferrer">
            <Text type="link">here</Text>
          </a>{' '}
          how to get started.
        </Text>
        <form onSubmit={handleSubmit(onSubmit)}>
          <Controller
            name={'onCallApiUrl'}
            control={control}
            rules={{ required: 'URL is required', validate: validateURL }}
            render={({ field }) => (
              <Field
                key={'Name'}
                label={'OnCall API URL'}
                invalid={Boolean(formState.errors.onCallApiUrl)}
                error={formState.errors.onCallApiUrl?.message}
              >
                <Input {...field} placeholder={'OnCall API URL'} data-testid="oncall-api-url-input" />
              </Field>
            )}
          />
          <Stack>
            {isPluginConnected && (
              <Button onClick={() => navigate(`${PLUGIN_ROOT}/${DEFAULT_PAGE}`)}>Open Grafana OnCall</Button>
            )}
            <Button
              type="submit"
              disabled={isSubmitButtonDisabled}
              data-testid="connect-plugin"
              variant={isPluginConnected ? 'secondary' : 'primary'}
            >
              {isPluginConnected ? 'Reconnect' : 'Connect'}
            </Button>
            <RenderConditionally
              shouldRender={isReinitializating}
              render={() => <LoadingPlaceholder text="" className={styles.spinner} />}
            />
          </Stack>
        </form>
      </>
    );

    const COMMON_CONFIG_ELEM_PARAMS = {
      startingElemPosition: '-6px',
    };

    const configElements = [
      {
        ...getCheckOrTextIcon(meta.enabled),
        expandedView: enablePluginExpandedView,
      },
      ...(getIsExternalServiceAccountFeatureAvailable()
        ? []
        : [
            {
              ...getCheckOrTextIcon(connectionStatus?.service_account_token?.ok),
              expandedView: serviceAccountTokenExpandedView,
            },
          ]),
      {
        ...getCheckOrTextIcon(connectionStatus?.oncall_api_url?.ok),
        expandedView: onCallApiUrlExpandedView,
      },
    ].map((elem) => ({ ...COMMON_CONFIG_ELEM_PARAMS, ...elem }));

    return (
      <div className={styles.configurationWrapper}>
        <Text type="secondary" className={styles.secondaryTitle}>
          This page will help you to connect OnCall backend and OnCall Grafana plugin.
        </Text>
        {showAlert && <PluginConfigAlert />}
        <CollapsibleTreeView className={styles.treeView} configElements={configElements} />
      </div>
    );
  }
);

const PluginConfigAlert = observer(() => {
  const {
    pluginStore: { connectionStatus, isPluginConnected },
  } = rootStore;
  const [showAlert, setShowAlert] = useState(true);

  useEffect(() => {
    setShowAlert(true);
  }, [connectionStatus]);

  if (!connectionStatus) {
    return null;
  }

  const errors = Object.values(connectionStatus)
    .filter(({ ok, error }) => !ok && Boolean(error) && error !== 'Not validated')
    .map(({ error }) => <li key={error}>{error}</li>);

  if (isPluginConnected) {
    return (
      <Alert severity="success" title="Plugin is connected">
        Go to{' '}
        <a href={PLUGIN_ROOT} rel="noreferrer">
          <Text type="link">Grafana OnCall</Text>
        </a>
      </Alert>
    );
  }
  return (
    <RenderConditionally
      shouldRender={showAlert}
      render={() => (
        <Alert severity="error" title="Plugin is not connected" onRemove={() => setShowAlert(false)}>
          <ol
            className={css`
              margin-bottom: 12px;
            `}
          >
            {errors}
          </ol>
          <a href={PLUGIN_CONFIG} rel="noreferrer" onClick={() => window.location.reload()}>
            <Text type="link">Reload</Text>
          </a>
        </Alert>
      )}
    />
  );
});

const getStyles = (theme: GrafanaTheme2) => ({
  configurationWrapper: css`
    width: 50vw;
  `,
  secondaryTitle: css`
    display: block;
    margin-bottom: 12px;
  `,
  spinner: css`
    margin-bottom: 0;
    & path {
      fill: ${theme.colors.text.primary};
    }
  `,
  treeView: css`
    & path {
      fill: ${theme.colors.success.text};
    }
    margin-bottom: 100px;
  `,
});
