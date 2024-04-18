import React, { useCallback } from 'react';

import { SelectableValue } from '@grafana/data';
import { Button, Drawer, Field, HorizontalGroup, Select, VerticalGroup, useStyles2 } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import Emoji from 'react-emoji-render';
import { Controller, FormProvider, useForm } from 'react-hook-form';
import { getUtilStyles } from 'styles/utils.styles';

import { GSelect } from 'containers/GSelect/GSelect';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { AlertReceiveChannelHelper } from 'models/alert_receive_channel/alert_receive_channel.helpers';
import { MaintenanceMode } from 'models/alert_receive_channel/alert_receive_channel.types';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization/authorization';
import { openNotification, showApiError } from 'utils/utils';

import styles from './MaintenanceForm.module.css';

const cx = cn.bind(styles);

interface MaintenanceFormProps {
  initialData: {
    alert_receive_channel_id?: ApiSchemas['AlertReceiveChannel']['id'];
  };
  onHide: () => void;
  onUpdate: () => void;
}

interface FormFields {
  alert_receive_channel_id: ApiSchemas['AlertReceiveChannel']['id'];
  mode: MaintenanceMode;
  duration: number;
}

export const MaintenanceForm = observer((props: MaintenanceFormProps) => {
  const { onUpdate, onHide, initialData = {} } = props;
  const { alertReceiveChannelStore } = useStore();

  const onSubmit = useCallback(async (data) => {
    try {
      await AlertReceiveChannelHelper.startMaintenanceMode(
        initialData.alert_receive_channel_id,
        data.mode,
        data.duration
      );
      onHide();
      onUpdate();
      openNotification('Maintenance has been started');
    } catch (err) {
      showApiError(err);
    }
  }, []);

  const formMethods = useForm<FormFields>({
    mode: 'onChange',
    defaultValues: { ...initialData },
  });

  const {
    handleSubmit,
    control,
    formState: { errors },
  } = formMethods;

  const utils = useStyles2(getUtilStyles);

  return (
    <Drawer width="640px" scrollableContent title="Start Maintenance Mode" onClose={onHide} closeOnMaskClick={false}>
      <div className={cx('content')} data-testid="maintenance-mode-drawer">
        <VerticalGroup>
          Start maintenance mode when performing scheduled maintenance or updates on the infrastructure, which may
          trigger false alarms.
          <FormProvider {...formMethods}>
            <form id="Maintenance" onSubmit={handleSubmit(onSubmit)} className={utils.width100}>
              <Controller
                name="alert_receive_channel_id"
                control={control}
                rules={{ required: 'Integration is required' }}
                render={({ field }) => (
                  <Field
                    label="Integration"
                    invalid={!!errors.alert_receive_channel_id}
                    error={errors.alert_receive_channel_id?.message}
                  >
                    <GSelect<ApiSchemas['AlertReceiveChannel']>
                      disabled
                      showSearch
                      items={alertReceiveChannelStore.items}
                      fetchItemsFn={alertReceiveChannelStore.fetchItems}
                      fetchItemFn={alertReceiveChannelStore.fetchItemById}
                      getSearchResult={() => AlertReceiveChannelHelper.getSearchResult(alertReceiveChannelStore)}
                      displayField="verbal_name"
                      valueField="id"
                      getOptionLabel={(item: SelectableValue) => <Emoji text={item?.label || ''} />}
                      value={field.value}
                      onChange={(value) => {
                        field.onChange(value);
                      }}
                    />
                  </Field>
                )}
              />
              <Controller
                name="mode"
                control={control}
                rules={{ required: 'Mode is required' }}
                render={({ field }) => (
                  <Field
                    label="Mode"
                    description="Choose maintenance mode: Debug (test routing and escalations without real notifications) or Maintenance (group alerts into one during infrastructure work)."
                    invalid={!!errors.mode}
                    error={errors.mode?.message}
                  >
                    <Select
                      placeholder="Choose mode"
                      value={field.value}
                      menuShouldPortal
                      options={[
                        {
                          value: MaintenanceMode.Debug,
                          label: 'Debug (silence all escalations)',
                        },
                        {
                          value: MaintenanceMode.Maintenance,
                          label: 'Maintenance (collect everything in one alert group)',
                        },
                      ]}
                      onChange={(option: SelectableValue) => {
                        field.onChange(option.value);
                      }}
                    />
                  </Field>
                )}
              />
              <Controller
                name="duration"
                control={control}
                rules={{ required: 'Duration is required' }}
                render={({ field }) => (
                  <Field
                    label="Duration"
                    description="Specify duration of the maintenance"
                    invalid={!!errors.duration}
                    error={errors.duration?.message}
                  >
                    <Select
                      placeholder="Choose duration"
                      value={field.value}
                      menuShouldPortal
                      options={[
                        {
                          value: 3600,
                          label: '1 hour',
                        },
                        {
                          value: 10800,
                          label: '3 hours',
                        },
                        {
                          value: 21600,
                          label: '6 hours',
                        },
                        {
                          value: 43200,
                          label: '12 hours',
                        },
                        {
                          value: 86400,
                          label: '24 hours',
                        },
                      ]}
                      onChange={(option: SelectableValue) => {
                        field.onChange(option.value);
                      }}
                    />
                  </Field>
                )}
              />
              <HorizontalGroup justify="flex-end">
                <Button variant="secondary" onClick={onHide}>
                  Cancel
                </Button>
                <WithPermissionControlTooltip userAction={UserActions.MaintenanceWrite}>
                  <Button type="submit" data-testid="create-maintenance-button">
                    Start
                  </Button>
                </WithPermissionControlTooltip>
              </HorizontalGroup>
            </form>
          </FormProvider>
        </VerticalGroup>
      </div>
    </Drawer>
  );
});
