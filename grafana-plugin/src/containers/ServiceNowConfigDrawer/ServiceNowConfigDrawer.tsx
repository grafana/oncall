import React from 'react';

import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { Drawer, Field, HorizontalGroup, Input, useStyles2, Button } from '@grafana/ui';
import { observer } from 'mobx-react';
import { parseUrl } from 'query-string';
import { Controller, FormProvider, useForm } from 'react-hook-form';

import { ActionKey } from 'models/loader/action-keys';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useCurrentIntegration } from 'pages/integration/OutgoingTab/OutgoingTab.hooks';
import { useStore } from 'state/useStore';
import { useIsLoading } from 'utils/hooks';
import { OmitReadonlyMembers } from 'utils/types';
import { openNotification } from 'utils/utils';

import { getCommonServiceNowConfigStyles } from './ServiceNow.styles';
import { ServiceNowAuthSection } from './ServiceNowAuthSection';
import { ServiceNowStatusSection } from './ServiceNowStatusSection';
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

  const currentIntegration = useCurrentIntegration();

  const formMethods = useForm<FormFields>({
    defaultValues: {
      additional_settings: { ...currentIntegration.additional_settings },
    },
    mode: 'onChange',
  });

  const {
    control,
    handleSubmit,
    formState: { errors },
  } = formMethods;

  const isLoading = useIsLoading(ActionKey.UPDATE_INTEGRATION);

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

              <ServiceNowAuthSection />
            </div>

            <div className={styles.border}>
              <ServiceNowStatusSection />
            </div>

            <div className={styles.border}>
              <ServiceNowTokenSection isDrawer />
            </div>

            <div className={styles.formButtons}>
              <HorizontalGroup justify="flex-end">
                <Button variant="secondary" onClick={onHide} disabled={isLoading}>
                  Close
                </Button>
                <Button variant="primary" type="submit" disabled={isLoading}>
                  Update
                </Button>
              </HorizontalGroup>
            </div>
          </form>
        </FormProvider>
      </Drawer>
    </>
  );

  function validateURL(urlFieldValue: string): string | boolean {
    return !parseUrl(urlFieldValue) ? 'Instance URL is invalid' : true;
  }

  async function onFormSubmit(formData: FormFields): Promise<void> {
    const data: OmitReadonlyMembers<ApiSchemas['AlertReceiveChannel']> = {
      ...currentIntegration,
      ...formData,
    };

    await alertReceiveChannelStore.update({ id: currentIntegration.id, data });

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
