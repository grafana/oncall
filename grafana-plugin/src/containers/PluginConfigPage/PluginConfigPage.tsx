import React from 'react';

import { css } from '@emotion/css';
import { GrafanaTheme2, PluginConfigPageProps, PluginMeta } from '@grafana/data';
import { config } from '@grafana/runtime';
import { Alert, Field, HorizontalGroup, Input, LoadingPlaceholder, useStyles2 } from '@grafana/ui';
import { observer } from 'mobx-react-lite';
import { Controller, useForm } from 'react-hook-form';
import { OnCallPluginMetaJSONData } from 'types';

import { Button } from 'components/Button/Button';
import { CollapsibleTreeView } from 'components/CollapsibleTreeView/CollapsibleTreeView';
import { Text } from 'components/Text/Text';
import { ActionKey } from 'models/loader/action-keys';
import { GrafanaApiClient } from 'network/grafana-api/http-client';
import { rootStore } from 'state/rootStore';
import { DOCS_ONCALL_OSS_INSTALL, DOCS_SERVICE_ACCOUNTS, getOnCallApiUrl } from 'utils/consts';
import { useOnMount } from 'utils/hooks';
import { validateURL } from 'utils/string';

type PluginConfigFormValues = {
  onCallApiUrl: string;
};

export const PluginConfigPage = observer(
  ({ plugin: { meta } }: PluginConfigPageProps<PluginMeta<OnCallPluginMetaJSONData>>) => {
    const {
      pluginStore: { updateOnCallApiUrlAndReinitializePlugin, connectionStatus, verifyPluginConnection },
      loaderStore,
    } = rootStore;
    const styles = useStyles2(getStyles);
    const { handleSubmit, control, formState } = useForm<PluginConfigFormValues>({
      mode: 'onChange',
      defaultValues: { onCallApiUrl: getOnCallApiUrl(meta) },
    });
    const isReinitializating = loaderStore.isLoading(ActionKey.REINITIALIZE_PLUGIN_WITH_NEW_API_URL);

    useOnMount(verifyPluginConnection);

    const onSubmit = async (values: PluginConfigFormValues) => {
      await updateOnCallApiUrlAndReinitializePlugin(values.onCallApiUrl);
    };

    return (
      <>
        <PluginConfigAlert />
        <Text.Title level={3}>Configure Grafana OnCall</Text.Title>
        <Text type="secondary" className={styles.secondaryTitle}>
          This page will help you to connect OnCall backend and OnCall Grafana plugin.
        </Text>
        <CollapsibleTreeView
          className={styles.treeView}
          configElements={[
            {
              ...(meta.enabled ? { customIcon: 'check' } : { isTextIcon: true }),
              startingElemPosition: '-6px',
              expandedView: () => (
                <>
                  <Text strong>Enable OnCall plugin</Text>
                  <Text type="secondary" className={styles.secondaryTitle}>
                    Make sure that OnCall plugin has been enabled.
                  </Text>
                </>
              ),
            },
            ...(config.featureToggles.externalServiceAccounts
              ? []
              : [
                  {
                    ...(connectionStatus?.service_account_token?.ok
                      ? { customIcon: 'check' as const }
                      : { isTextIcon: true }),
                    startingElemPosition: '-6px',
                    expandedView: () => (
                      <>
                        <Text strong>Service account user allows to connect OnCall plugin to Grafana. </Text>
                        <Text type="secondary" className={styles.secondaryTitle}>
                          Make sure that OnCall plugin has been enabled.{' '}
                          <a href={DOCS_SERVICE_ACCOUNTS} target="_blank" rel="noreferrer">
                            <Text type="link">Read more</Text>
                          </a>
                        </Text>
                        <Button
                          variant="secondary"
                          onClick={() => GrafanaApiClient.recreateGrafanaTokenAndSaveInPluginSettings()}
                        >
                          Re-create
                        </Button>
                      </>
                    ),
                  },
                ]),
            {
              ...(connectionStatus?.oncall_api_url?.ok ? { customIcon: 'check' as const } : { isTextIcon: true }),
              startingElemPosition: '-6px',
              expandedView: () => (
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
                      rules={{ required: 'OnCall API URL is required', validate: validateURL }}
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
                      <Button type="submit" disabled={!formState.isValid || !meta.enabled}>
                        {meta.jsonData?.onCallApiUrl ? 'Reconnect' : 'Connect'}
                      </Button>
                      {isReinitializating && <LoadingPlaceholder text="" className={styles.spinner} />}
                    </HorizontalGroup>
                  </form>
                </>
              ),
            },
          ]}
        />
      </>
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
  return isPluginConnected ? (
    <Alert severity="success" title="Plugin is connected" />
  ) : (
    <Alert severity="error" title="Plugin is not connected">
      <ol>
        {Object.values(connectionStatus)
          .filter(({ ok, error }) => !ok && Boolean(error))
          .map(({ error }, idx) => (
            <li key={error}>
              {idx + 1}. {error}
            </li>
          ))}
      </ol>
    </Alert>
  );
});

const getStyles = (theme: GrafanaTheme2) => ({
  secondaryTitle: css`
    display: block;
    margin: 12px 0;
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
