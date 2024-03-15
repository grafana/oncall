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
import { observer } from 'mobx-react';
import { Controller, useForm } from 'react-hook-form';

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

interface ServiceNowConfigurationDrawerProps {
  onHide(): void;
}

enum OnCallAGStatus {
  Firing = 'Firing',
  Resolved = 'Resolved',
  Silenced = 'Silenced',
  Acknowledged = 'Acknowledged',
}

interface FormFields {
  additional_settings: ApiSchemas['AlertReceiveChannel']['additional_settings'];
}

interface StatusMapping {
  [OnCallAGStatus.Firing]?: string;
  [OnCallAGStatus.Resolved]?: string;
  [OnCallAGStatus.Silenced]?: string;
  [OnCallAGStatus.Acknowledged]?: string;
}

export const ServiceNowConfigDrawer: React.FC<ServiceNowConfigurationDrawerProps> = observer(({ onHide }) => {
  const styles = useStyles2(getStyles);
  const { alertReceiveChannelStore } = useStore();

  const integration = useCurrentIntegration();

  const [isAuthTestRunning, setIsAuthTestRunning] = useState(false);
  const [authTestResult, setAuthTestResult] = useState(undefined);
  const [statusMapping, setStatusMapping] = useState<StatusMapping>({});

  const {
    control,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<FormFields>({
    defaultValues: {
      additional_settings: { ...integration.additional_settings },
    },
    mode: 'onChange',
  });

  const serviceNowAPIToken = 'http://url.com';
  const isLoading = useIsLoading(ActionKey.UPDATE_INTEGRATION);

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
                      <Controller
                        name={'additional_settings.state_mapping.firing'}
                        control={control}
                        render={({ field }) => (
                          <Select
                            {...field}
                            key="state_mapping.firing"
                            menuShouldPortal
                            className="select control"
                            options={getAvailableStatusOptions(OnCallAGStatus.Firing)}
                            onChange={(option: SelectableValue) => {
                              onStatusSelectChange(option, OnCallAGStatus.Firing);
                              setValue('additional_settings.state_mapping.firing', null);
                            }}
                            {...selectCommonProps}
                          />
                        )}
                      />
                    </td>
                  </tr>

                  <tr>
                    <td>Acknowledged</td>

                    <td>
                      <Controller
                        name={'additional_settings.state_mapping.acknowledged'}
                        control={control}
                        render={({ field }) => (
                          <Select
                            {...field}
                            menuShouldPortal
                            className="select control"
                            disabled={false}
                            options={getAvailableStatusOptions(OnCallAGStatus.Acknowledged)}
                            onChange={(option: SelectableValue) => {
                              onStatusSelectChange(option, OnCallAGStatus.Acknowledged);
                              setValue('additional_settings.state_mapping.acknowledged', null);
                            }}
                            {...selectCommonProps}
                          />
                        )}
                      />
                    </td>
                  </tr>

                  <tr>
                    <td>Resolved</td>
                    <td>
                      <Controller
                        name={'additional_settings.state_mapping.resolved'}
                        control={control}
                        render={({ field }) => (
                          <Select
                            {...field}
                            menuShouldPortal
                            className="select control"
                            disabled={false}
                            options={getAvailableStatusOptions(OnCallAGStatus.Resolved)}
                            onChange={(option: SelectableValue) => {
                              onStatusSelectChange(option, OnCallAGStatus.Resolved);
                              setValue('additional_settings.state_mapping.resolved', null);
                            }}
                            {...selectCommonProps}
                          />
                        )}
                      />
                    </td>
                  </tr>

                  <tr>
                    <td>Silenced</td>
                    <td>
                      <Controller
                        name={'additional_settings.state_mapping.silenced'}
                        control={control}
                        render={({ field }) => (
                          <Select
                            {...field}
                            menuShouldPortal
                            className="select control"
                            disabled={false}
                            options={getAvailableStatusOptions(OnCallAGStatus.Silenced)}
                            onChange={(option: SelectableValue) => {
                              onStatusSelectChange(option, OnCallAGStatus.Silenced);
                              setValue('additional_settings.state_mapping.silenced', null);
                            }}
                            {...selectCommonProps}
                          />
                        )}
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
              <Button variant="primary" type="submit" disabled={isLoading}>
                {isLoading ? <LoadingPlaceholder className={styles.loader} text="Loading..." /> : 'Update'}
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
