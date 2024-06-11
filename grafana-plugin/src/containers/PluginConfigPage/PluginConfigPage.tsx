import React from 'react';

import { css } from '@emotion/css';
import { GrafanaTheme2, PluginConfigPageProps, PluginMeta } from '@grafana/data';
import { Field, HorizontalGroup, Input, useStyles2 } from '@grafana/ui';
import { observer } from 'mobx-react-lite';
import { Controller, useForm } from 'react-hook-form';
import { OnCallPluginMetaJSONData } from 'types';

import { Button } from 'components/Button/Button';
import { CollapsibleTreeView } from 'components/CollapsibleTreeView/CollapsibleTreeView';
import { Text } from 'components/Text/Text';
import { DOCS_ONCALL_OSS_INSTALL, DOCS_SERVICE_ACCOUNTS, getOnCallApiUrl } from 'utils/consts';
import { validateURL } from 'utils/string';

type PluginConfigFormValues = {
  onCallApiUrl: string;
};

export const PluginConfigPage = observer((props: PluginConfigPageProps<PluginMeta<OnCallPluginMetaJSONData>>) => {
  const styles = useStyles2(getStyles);
  const { handleSubmit, control, formState } = useForm<PluginConfigFormValues>({
    mode: 'onChange',
    defaultValues: { onCallApiUrl: getOnCallApiUrl(props.plugin.meta) },
  });

  const onSubmit = (values: PluginConfigFormValues) => {
    // eslint-disable-next-line no-console
    console.log(values);
  };

  return (
    <>
      <Text.Title level={3}>Configure Grafana OnCall</Text.Title>
      <Text type="secondary" className={styles.secondaryTitle}>
        This page will help you to connect OnCall backend and OnCall Grafana plugin.
      </Text>
      <CollapsibleTreeView
        className={styles.treeView}
        configElements={[
          {
            ...(true ? { customIcon: 'check' } : { isTextIcon: true }),
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
          {
            ...(true ? { customIcon: 'check' } : { isTextIcon: true }),
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
                <Button variant="secondary">Re-create</Button>
              </>
            ),
          },
          {
            ...(true ? { customIcon: 'check' } : { isTextIcon: true }),
            startingElemPosition: '-6px',
            expandedView: () => (
              <>
                <Text strong>Launch OnCall backend</Text>
                <Text type="secondary" className={styles.secondaryTitle}>
                  Run hobby, dev or production backend. See{' '}
                  <a href={DOCS_ONCALL_OSS_INSTALL} target="_blank" rel="noreferrer">
                    <Text type="link">here</Text>
                  </a>{' '}
                  how to get started.
                </Text>
              </>
            ),
          },
          {
            ...(true ? { customIcon: 'check' } : { isTextIcon: true }),
            startingElemPosition: '-6px',
            expandedView: () => (
              <>
                <Text strong>Let us know the backend URL for your OnCall API</Text>
                <Text type="secondary" className={styles.secondaryTitle}>
                  OnCall backend must be reachable from your Grafana Installation.
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
                    <Button type="submit" disabled={!formState.isValid}>
                      Connect
                    </Button>
                    {/* {config.featureToggles.externalServiceAccounts && (
                      <Button variant="secondary">Recreate service account</Button>
                    )} */}
                  </HorizontalGroup>
                </form>
              </>
            ),
          },
        ]}
      />
    </>
  );
});

const getStyles = (theme: GrafanaTheme2) => ({
  secondaryTitle: css`
    display: block;
    margin: 12px 0;
  `,
  treeView: css`
    & path {
      fill: ${theme.colors.success.text};
    }
    margin-bottom: 100px;
  `,
});
