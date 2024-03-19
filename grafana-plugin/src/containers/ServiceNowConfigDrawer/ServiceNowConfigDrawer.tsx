import React, { useEffect, useState } from 'react';

import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import {
  Drawer,
  Field,
  HorizontalGroup,
  Input,
  VerticalGroup,
  Icon,
  useStyles2,
  Button,
  LoadingPlaceholder,
} from '@grafana/ui';
import { observer } from 'mobx-react';
import { Controller, FormProvider, useForm } from 'react-hook-form';

import { IntegrationInputField } from 'components/IntegrationInputField/IntegrationInputField';
import { RenderConditionally } from 'components/RenderConditionally/RenderConditionally';
import { Text } from 'components/Text/Text';
import { ActionKey } from 'models/loader/action-keys';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useCurrentIntegration } from 'pages/integration/OutgoingTab/OutgoingTab.hooks';
import { useStore } from 'state/useStore';
import { URL_REGEX } from 'utils/consts';
import { useIsLoading } from 'utils/hooks';
import { OmitReadonlyMembers } from 'utils/types';
import { openNotification } from 'utils/utils';

import { getCommonServiceNowConfigStyles } from './ServiceNow.styles';
import { ServiceNowStatusSection, ServiceNowStatusMapping } from './ServiceNowStatusSection';
import { ServiceNowTokenSection } from './ServiceNowTokenSection';

interface ServiceNowConfigurationDrawerProps {
  onHide(): void;
}

interface FormFields {
  additional_settings: ApiSchemas['AlertReceiveChannel']['additional_settings'];
}

export const ServiceNowConfigDrawer: React.FC<ServiceNowConfigurationDrawerProps> = observer(({ onHide }) => {
  const styles = useStyles2(getStyles);
  const { alertReceiveChannelStore } = useStore();

  const integration = useCurrentIntegration();

  const [isAuthTestRunning, setIsAuthTestRunning] = useState(false);
  const [authTestResult, setAuthTestResult] = useState(undefined);
  const [statusMapping, setStatusMapping] = useState<ServiceNowStatusMapping>({});

  const formMethods = useForm<FormFields>({
    defaultValues: {
      additional_settings: { ...integration.additional_settings },
    },
    mode: 'onChange',
  });

  const {
    control,
    handleSubmit,
    formState: { errors },
  } = formMethods;

  const isLoading = useIsLoading(ActionKey.UPDATE_INTEGRATION);

  useEffect(() => {
    (async () => {
      await alertReceiveChannelStore.fetchServiceNowStatusList({ id: integration.id });
    })();
  }, []);

  return (
    <>
      <Drawer title="ServiceNow configuration" onClose={onHide} closeOnMaskClick={false} size="md">
        <FormProvider {...formMethods}>
          <form onSubmit={handleSubmit(onFormSubmit)}>
            <div className={styles.border}>
              <Controller
                name={'additional_settings.instance_url'}
                control={control}
                rules={{ required: 'Instance URL is required', validate: validateURL }}
                render={({ field }) => (
                  <Field
                    key={'InstanceURL'}
                    label={'Instance URL'}
                    invalid={!!errors.additional_settings?.instance_url}
                    error={errors.additional_settings?.instance_url?.message}
                  >
                    <Input {...field} />
                  </Field>
                )}
              />

              <Controller
                name={'additional_settings.username'}
                control={control}
                rules={{ required: 'Username is required' }}
                render={({ field }) => (
                  <Field
                    key={'AuthUsername'}
                    label={'Username'}
                    invalid={!!errors.additional_settings?.username}
                    error={errors.additional_settings?.username?.message}
                  >
                    <Input {...field} />
                  </Field>
                )}
              />

              <Controller
                name={'additional_settings.password'}
                control={control}
                rules={{ required: 'Password is required' }}
                render={({ field }) => (
                  <Field
                    key={'AuthPassword'}
                    label={'Password'}
                    invalid={!!errors.additional_settings?.password}
                    error={errors.additional_settings?.password?.message}
                  >
                    <Input {...field} type="password" />
                  </Field>
                )}
              />

              <HorizontalGroup>
                <Button className={''} variant="secondary" onClick={onAuthTest}>
                  Test
                </Button>
                <div>
                  <RenderConditionally shouldRender={isAuthTestRunning}>
                    <LoadingPlaceholder text="Loading" className={styles.loader} />
                  </RenderConditionally>

                  <RenderConditionally shouldRender={!isAuthTestRunning && authTestResult !== undefined}>
                    <HorizontalGroup align="center" justify="center">
                      <Text type="primary">{authTestResult ? 'Connection OK' : 'Connection failed'}</Text>
                      <Icon name={authTestResult ? 'check-circle' : 'x'} />
                    </HorizontalGroup>
                  </RenderConditionally>
                </div>
              </HorizontalGroup>
            </div>

            <div className={styles.border}>
              <ServiceNowStatusSection setStatusMapping={setStatusMapping} statusMapping={statusMapping} />
            </div>

            <div className={styles.border}>
              <VerticalGroup>
                <HorizontalGroup spacing="xs" align="center">
                  <Text type="primary" strong>
                    Labels Mapping
                  </Text>
                  <Icon name="info-circle" />
                </HorizontalGroup>

                <Text>
                  Description for such object and{' '}
                  <a href={'#'} target="_blank" rel="noreferrer">
                    <Text type="link">link to documentation</Text>
                  </a>
                </Text>
              </VerticalGroup>
            </div>

            <div className={styles.border}>
              <ServiceNowTokenSection />
            </div>

            <div className={styles.formButtons}>
              <HorizontalGroup justify="flex-end">
                <Button variant="secondary" onClick={onHide}>
                  Close
                </Button>
                <Button variant="primary" type="submit" disabled={isLoading}>
                  {isLoading ? <LoadingPlaceholder className={styles.loader} text="Loading..." /> : 'Update'}
                </Button>
              </HorizontalGroup>
            </div>
          </form>
        </FormProvider>
      </Drawer>
    </>
  );

  function onTokenRegenerate() {
    // Call API and reset token
  }

  function onAuthTest() {
    return new Promise(() => {
      setIsAuthTestRunning(true);
      setTimeout(() => {
        setIsAuthTestRunning(false);
        setAuthTestResult(true);
      }, 500);
    });
  }

  function validateURL(urlFieldValue: string): string | boolean {
    const regex = new RegExp(URL_REGEX, 'i');
    return !regex.test(urlFieldValue) ? 'Instance URL is invalid' : true;
  }

  async function onFormSubmit(formData: FormFields): Promise<void> {
    const data: OmitReadonlyMembers<ApiSchemas['AlertReceiveChannel']> = {
      ...integration,
      ...formData,
    };

    await alertReceiveChannelStore.update({ id: integration.id, data });

    openNotification('ServiceNow configuration has been updated');

    onHide();
  }
});

const getStyles = (theme: GrafanaTheme2) => {
  return {
    ...getCommonServiceNowConfigStyles(theme),

    loader: css`
      margin-bottom: 0;
    `,

    formButtons: css`
      padding-bottom: 24px;
    `,
  };
};
