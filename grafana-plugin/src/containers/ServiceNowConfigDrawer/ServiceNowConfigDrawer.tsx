import React, { useEffect, useState } from 'react';

import { css } from '@emotion/css';
import { GrafanaTheme2, SelectableValue } from '@grafana/data';
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
  Select,
} from '@grafana/ui';
import { Controller, useForm } from 'react-hook-form';

import { Text } from 'components/Text/Text';
import { RenderConditionally } from 'components/RenderConditionally/RenderConditionally';
import { useStore } from 'state/useStore';
import { observer } from 'mobx-react';

interface ServiceNowConfigurationDrawerProps {
  onHide(): void;
}

enum FormFieldKeys {
  ServiceNowUrl = 'servicenow_url',
  AuthUsername = 'auth_username',
  AuthPassword = 'auth_password',
}

enum OnCallAGStatus {
  Resolved,
  Silenced,
  Acknowledged,
  // TODO add remaining
}

interface FormFields {
  [FormFieldKeys.ServiceNowUrl]: string;
  [FormFieldKeys.AuthUsername]: string;
  [FormFieldKeys.AuthPassword]: string;
}

export const ServiceNowConfigDrawer: React.FC<ServiceNowConfigurationDrawerProps> = observer(({ onHide }) => {
  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<FormFields>({ mode: 'onChange' });

  const styles = useStyles2(getStyles);
  const { alertReceiveChannelStore } = useStore();
  const [isAuthTestRunning, setIsAuthTestRunning] = useState(false);
  const [authTestResult, setAuthTestResult] = useState(undefined);

  useEffect(() => {
    (async () => {
      await alertReceiveChannelStore.fetchServiceNowListOfStatus();
    })();
  }, []);

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
            <VerticalGroup spacing="md">
              <HorizontalGroup spacing="xs" align="center">
                <Text type="primary" size="small">
                  Status Mapping
                </Text>
                <Icon name="info-circle" />
              </HorizontalGroup>

              <table className={'filter-table'}>
                <thead>
                  <tr>
                    <th>OnCall Alert group status</th>
                    <th>ServiceNow incident status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Firing</td>

                    <td>
                      <Select
                        menuShouldPortal
                        className="select control"
                        disabled={false}
                        value={undefined}
                        options={getAvailableStatusOptions()}
                        onChange={onStatusSelectChange}
                      />
                    </td>
                  </tr>

                  <tr>
                    <td>Acknowledged</td>

                    <td>
                      <Select
                        menuShouldPortal
                        className="select control"
                        disabled={false}
                        value={undefined}
                        options={getAvailableStatusOptions()}
                        onChange={onStatusSelectChange}
                      />
                    </td>
                  </tr>

                  <tr>
                    <td>Resolved</td>
                    <td>
                      <Select
                        menuShouldPortal
                        className="select control"
                        disabled={false}
                        value={undefined}
                        options={getAvailableStatusOptions()}
                        onChange={onStatusSelectChange}
                      />
                    </td>
                  </tr>

                  <tr>
                    <td>Silenced</td>
                    <td>
                      <Select
                        menuShouldPortal
                        className="select control"
                        disabled={false}
                        value={undefined}
                        options={getAvailableStatusOptions()}
                        onChange={onStatusSelectChange}
                      />
                    </td>
                  </tr>
                </tbody>
              </table>
            </VerticalGroup>
          </div>

          <div className={styles.border}>
            <VerticalGroup>
              <HorizontalGroup spacing="xs" align="center">
                <Text type="primary" size="small">
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
            <VerticalGroup>
              <HorizontalGroup spacing="xs" align="center">
                <Text type="primary" size="small">
                  ServiceNow API Token
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
        </form>
      </Drawer>
    </>
  );

  function getAvailableStatusOptions() {
    return (alertReceiveChannelStore.serviceNowStatusList || []).map((status) => ({
      value: status.id,
      label: status.name,
    }));
  }

  function onStatusSelectChange(option: SelectableValue) {}

  function onAuthTest() {
    return new Promise(() => {
      setIsAuthTestRunning(true);
      setTimeout(() => {
        setIsAuthTestRunning(false);
        setAuthTestResult(true);
      }, 500);
    });
  }

  function validateURL() {
    return true;
  }

  function onFormSubmit(formData: FormFields): Promise<void> {
    return undefined;
  }
});

const getStyles = (theme: GrafanaTheme2) => {
  return {
    border: css`
      padding: 12px;
      margin-bottom: 24px;
      border: 1px solid ${theme.colors.border.weak};
      border-radius: ${theme.shape.radius.default};
    `,

    loader: css`
      margin-bottom: 0;
    `,
  };
};
