import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { Drawer, Field, Input, useStyles2 } from '@grafana/ui';
import React from 'react';
import { Controller, useForm } from 'react-hook-form';

interface ServiceNowConfigurationDrawerProps {
  onHide(): void;
}

enum FormFieldKeys {
  ServiceNowUrl = 'servicenow_url',
  AuthUsername = 'auth_username',
  AuthPassword = 'auth_password',
}

interface FormFields {
  [FormFieldKeys.ServiceNowUrl]: string;
  [FormFieldKeys.AuthUsername]: string;
  [FormFieldKeys.AuthPassword]: string;
}

export const ServiceNowConfigDrawer: React.FC<ServiceNowConfigurationDrawerProps> = ({ onHide }) => {
  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<FormFields>({ mode: 'onChange' });

  const styles = useStyles2(getStyles);

  return (
    <>
      <Drawer title="ServiceNow configuration" onClose={onHide} closeOnMaskClick={false} size="md">
        <form onSubmit={handleSubmit(onFormSubmit)}>
          <div className={styles.border}>
            <Controller
              name={FormFieldKeys.ServiceNowUrl}
              control={control}
              rules={{ required: 'Instance URL is required', validate: validateURL }}
              render={({ field }) => (
                <Field
                  key={'InstanceURL'}
                  label={'Instance URL'}
                  invalid={!!errors[FormFieldKeys.ServiceNowUrl]}
                  error={errors[FormFieldKeys.ServiceNowUrl]?.message}
                >
                  <Input {...field} />
                </Field>
              )}
            />

            <Controller
              name={FormFieldKeys.AuthUsername}
              control={control}
              rules={{ required: 'Username is required' }}
              render={({ field }) => (
                <Field
                  key={'AuthUsername'}
                  label={'Username'}
                  invalid={!!errors[FormFieldKeys.AuthUsername]}
                  error={errors[FormFieldKeys.AuthUsername]?.message}
                >
                  <Input {...field} />
                </Field>
              )}
            />

            <Controller
              name={FormFieldKeys.AuthPassword}
              control={control}
              rules={{ required: 'Password is required' }}
              render={({ field }) => (
                <Field
                  key={'AuthPassword'}
                  label={'Password'}
                  invalid={!!errors[FormFieldKeys.AuthPassword]}
                  error={errors[FormFieldKeys.AuthPassword]?.message as string}
                >
                  <Input {...field} type="password" />
                </Field>
              )}
            />
          </div>
        </form>
      </Drawer>
    </>
  );

  function validateURL() {
    return true;
  }

  function onFormSubmit(formData: FormFields): Promise<void> {
    return undefined;
  }
};

const getStyles = (theme: GrafanaTheme2) => {
  return {
    border: css`
      padding: 12px;
      margin-bottom: 24px;
      border: 1px solid ${theme.colors.border.weak};
      border-radius: ${theme.shape.radius.default};
    `,
  };
};
