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
  SelectBaseProps,
} from '@grafana/ui';
import { Controller, useForm } from 'react-hook-form';

import { Text } from 'components/Text/Text';
import { RenderConditionally } from 'components/RenderConditionally/RenderConditionally';
import { useStore } from 'state/useStore';
import { observer } from 'mobx-react';
import { IntegrationInputField } from 'components/IntegrationInputField/IntegrationInputField';
import { toJS } from 'mobx';

interface ServiceNowConfigurationDrawerProps {
  onHide(): void;
}

enum FormFieldKeys {
  ServiceNowUrl = 'servicenow_url',
  AuthUsername = 'auth_username',
  AuthPassword = 'auth_password',
}

enum OnCallAGStatus {
  Firing = 'Firing',
  Resolved = 'Resolved',
  Silenced = 'Silenced',
  Acknowledged = 'Acknowledged',
}

interface FormFields {
  [FormFieldKeys.ServiceNowUrl]: string;
  [FormFieldKeys.AuthUsername]: string;
  [FormFieldKeys.AuthPassword]: string;
}

interface StatusMapping {
  // TODO: Can this be changed to keyof usage?
  [OnCallAGStatus.Firing]?: string;
  [OnCallAGStatus.Resolved]?: string;
  [OnCallAGStatus.Silenced]?: string;
  [OnCallAGStatus.Acknowledged]?: string;
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

  const [statusMapping, setStatusMapping] = useState<StatusMapping>({});

  const serviceNowAPIToken = 'http://url.com';

  useEffect(() => {
    (async () => {
      await alertReceiveChannelStore.fetchServiceNowListOfStatus();
    })();
  }, []);

  const selectCommonProps: Partial<SelectBaseProps<any>> = {
    backspaceRemovesValue: true,
    isClearable: true,
    placeholder: 'Not Selected',
  };

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
                        options={getAvailableStatusOptions(OnCallAGStatus.Firing)}
                        onChange={(option: SelectableValue) => onStatusSelectChange(option, OnCallAGStatus.Firing)}
                        {...selectCommonProps}
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
                        options={getAvailableStatusOptions(OnCallAGStatus.Acknowledged)}
                        onChange={(option: SelectableValue) =>
                          onStatusSelectChange(option, OnCallAGStatus.Acknowledged)
                        }
                        {...selectCommonProps}
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
                        options={getAvailableStatusOptions(OnCallAGStatus.Resolved)}
                        onChange={(option: SelectableValue) => onStatusSelectChange(option, OnCallAGStatus.Resolved)}
                        {...selectCommonProps}
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
                        options={getAvailableStatusOptions(OnCallAGStatus.Silenced)}
                        onChange={(option: SelectableValue) => onStatusSelectChange(option, OnCallAGStatus.Silenced)}
                        {...selectCommonProps}
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

              <div className={styles.tokenContainer}>
                <IntegrationInputField
                  inputClassName={styles.tokenInput}
                  iconsClassName={styles.tokenIcons}
                  value={serviceNowAPIToken}
                  showExternal={false}
                  isMasked
                />
                <Button variant="secondary" onClick={onTokenRegenerate}>
                  Regenerate
                </Button>
              </div>
            </VerticalGroup>
          </div>

          <div className={styles.formButtons}>
            <HorizontalGroup justify="flex-end">
              <Button variant="secondary" onClick={onHide}>
                Close
              </Button>
              <Button variant="primary" type="submit">
                Update
              </Button>
            </HorizontalGroup>
          </div>
        </form>
      </Drawer>
    </>
  );

  function onTokenRegenerate() {
    // Call API and reset token
  }

  function getAvailableStatusOptions(currentAction: OnCallAGStatus) {
    const keys = Object.keys(statusMapping);
    const values = keys.map((k) => statusMapping[k]).filter(Boolean);

    return (alertReceiveChannelStore.serviceNowStatusList || [])
      .filter((status) => values.indexOf(status.name) === -1 || statusMapping[currentAction] === status.name)
      .map((status) => ({
        value: status.id,
        label: status.name,
      }));
  }

  function onStatusSelectChange(option: SelectableValue, action: OnCallAGStatus) {
    setStatusMapping({
      ...statusMapping,
      [action]: option?.label,
    });
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

  function validateURL() {
    return true;
  }

  function onFormSubmit(formData: FormFields): Promise<void> {
    return undefined;
  }
});

const getStyles = (theme: GrafanaTheme2) => {
  return {
    tokenContainer: css`
      display: flex;
      width: 100%;
      gap: 8px;
    `,

    tokenInput: css`
      height: 32px !important;
      padding-top: 4px !important;
    `,

    tokenIcons: css`
      top: 10px !important;
    `,

    border: css`
      padding: 12px;
      margin-bottom: 24px;
      border: 1px solid ${theme.colors.border.weak};
      border-radius: ${theme.shape.radius.default};
    `,

    loader: css`
      margin-bottom: 0;
    `,

    formButtons: css`
      padding-bottom: 24px;
    `,
  };
};
