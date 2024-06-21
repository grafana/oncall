import React from 'react';

import { css } from '@emotion/css';
import { GrafanaTheme2, PluginConfigPageProps, PluginMeta } from '@grafana/data';
import { Alert, Field, HorizontalGroup, Input, LoadingPlaceholder, useStyles2, VerticalGroup } from '@grafana/ui';
import { observer } from 'mobx-react-lite';
import { Controller, useForm } from 'react-hook-form';
import { OnCallPluginMetaJSONData } from 'types';

import { Button } from 'components/Button/Button';
import { CollapsibleTreeView } from 'components/CollapsibleTreeView/CollapsibleTreeView';
import { Text } from 'components/Text/Text';
import { ActionKey } from 'models/loader/action-keys';
import { rootStore } from 'state/rootStore';
import {
  DOCS_ONCALL_OSS_INSTALL,
  DOCS_SERVICE_ACCOUNTS,
  PLUGIN_CONFIG,
  PLUGIN_ROOT,
  REQUEST_HELP_URL,
} from 'utils/consts';
import { useOnMount } from 'utils/hooks';
import { validateURL } from 'utils/string';
import { getIsExternalServiceAccountFeatureAvailable, getIsRunningOpenSourceVersion } from 'utils/utils';

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
    <VerticalGroup>
      <Text.Title level={3} className="u-margin-bottom-md">
        Configure Grafana OnCall
      </Text.Title>
      {props.plugin.meta.enabled && <PluginConfigAlert />}
      {getIsRunningOpenSourceVersion() ? <OSSPluginConfigPage {...props} /> : <CloudPluginConfigPage />}
    </VerticalGroup>
  );
});

const CloudPluginConfigPage = observer(() => {
  const {
    pluginStore: { isPluginConnected },
  } = rootStore;
  const styles = useStyles2(getStyles);

  return (
    <>
      <Text type="secondary" className={styles.secondaryTitle}>
        This is a cloud-managed configuration.
      </Text>
      {!isPluginConnected && <Button onClick={() => window.open(REQUEST_HELP_URL, '_blank')}>Request help</Button>}
    </>
  );
});

const OSSPluginConfigPage = observer(
  ({ plugin: { meta } }: PluginConfigPageProps<PluginMeta<OnCallPluginMetaJSONData>>) => {
    const {
      pluginStore: {
        updatePluginSettingsAndReinitializePlugin,
        connectionStatus,
        recreateServiceAccountAndRecheckPluginStatus,
        isPluginConnected,
        appliedOnCallApiUrl,
      },
      loaderStore,
    } = rootStore;
    const styles = useStyles2(getStyles);
    const { handleSubmit, control, formState } = useForm<PluginConfigFormValues>({
      mode: 'onChange',
      values: { onCallApiUrl: appliedOnCallApiUrl },
    });
    const isReinitializating = loaderStore.isLoading(ActionKey.PLUGIN_UPDATE_SETTINGS_AND_REINITIALIZE);
    const isRecreatingServiceAccount = loaderStore.isLoading(ActionKey.PLUGIN_RECREATE_SERVICE_ACCOUNT);

    const isSubmitButtonDisabled = !formState.isValid || !meta.enabled || isReinitializating;

    const onSubmit = async (values: PluginConfigFormValues) => {
      await updatePluginSettingsAndReinitializePlugin({
        currentJsonData: meta.jsonData,
        newJsonData: { onCallApiUrl: values.onCallApiUrl },
      });
    };

    const getCheckOrTextIcon = (isOk: boolean) => (isOk ? { customIcon: 'check' as const } : { isTextIcon: true });

    const enablePluginExpandedView = () => (
      <>
        <Text strong>Enable OnCall plugin</Text>
        <Text type="secondary" className={styles.secondaryTitle}>
          Make sure that OnCall plugin has been enabled.
        </Text>
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
        <HorizontalGroup>
          <Button
            variant="secondary"
            onClick={recreateServiceAccountAndRecheckPluginStatus}
            data-testid="recreate-service-account"
          >
            Re-create
          </Button>
          {isRecreatingServiceAccount && <LoadingPlaceholder text="" className={styles.spinner} />}
        </HorizontalGroup>
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
          <HorizontalGroup>
            <Button type="submit" disabled={isSubmitButtonDisabled} data-testid="connect-plugin">
              {isPluginConnected ? 'Reconnect' : 'Connect'}
            </Button>
            {isReinitializating && <LoadingPlaceholder text="" className={styles.spinner} />}
          </HorizontalGroup>
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
      <div>
        <Text type="secondary" className={styles.secondaryTitle}>
          This page will help you to connect OnCall backend and OnCall Grafana plugin.
        </Text>
        <CollapsibleTreeView className={styles.treeView} configElements={configElements} />
      </div>
    );
  }
);

const PluginConfigAlert = observer(() => {
  const {
    pluginStore: { connectionStatus, isPluginConnected },
  } = rootStore;

  if (!connectionStatus) {
    return null;
  }
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
    <Alert severity="error" title="Plugin is not connected">
      <ol className="u-margin-bottom-md">
        {Object.values(connectionStatus)
          .filter(({ ok, error }) => !ok && Boolean(error) && error !== 'Not validated')
          .map(({ error }, idx) => (
            <li key={error}>
              {idx + 1}. {error}
            </li>
          ))}
      </ol>
      <a href={PLUGIN_CONFIG} rel="noreferrer" onClick={() => window.location.reload()}>
        <Text type="link">Reload</Text>
      </a>
    </Alert>
  );
});

const getStyles = (theme: GrafanaTheme2) => ({
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
