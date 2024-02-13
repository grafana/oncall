import React, { useCallback, useMemo } from 'react';

import { Button, Drawer, HorizontalGroup, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { cloneDeep } from 'lodash-es';
import { observer } from 'mobx-react';

import { GForm } from 'components/GForm/GForm';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { AlertReceiveChannelHelper } from 'models/alert_receive_channel/alert_receive_channel.helpers';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization/authorization';
import { openNotification, showApiError } from 'utils/utils';

import { getForm } from './MaintenanceForm.config';

import styles from './MaintenanceForm.module.css';

const cx = cn.bind(styles);

interface MaintenanceFormProps {
  initialData: {
    alert_receive_channel_id?: ApiSchemas['AlertReceiveChannel']['id'];
    disabled?: boolean;
  };
  onHide: () => void;
  onUpdate: () => void;
}

export const MaintenanceForm = observer((props: MaintenanceFormProps) => {
  const { onUpdate, onHide, initialData = {} } = props;
  const { alertReceiveChannelStore } = useStore();
  const form = useMemo(() => getForm(alertReceiveChannelStore), [alertReceiveChannelStore]);
  const maintenanceForm = useMemo(() => (initialData.disabled ? cloneDeep(form) : form), [initialData]);

  const handleSubmit = useCallback(async (data) => {
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

  if (initialData.disabled) {
    const alertReceiveChannelIdField = maintenanceForm.fields.find((f) => f.name === 'alert_receive_channel_id');

    if (alertReceiveChannelIdField) {
      // Integration page requires this field to be preset and disabled, therefore we add extra field `disabled` for the cloned form
      alertReceiveChannelIdField.extra.disabled = true;
    }
  }

  return (
    <Drawer width="640px" scrollableContent title="Start Maintenance Mode" onClose={onHide} closeOnMaskClick={false}>
      <div className={cx('content')} data-testid="maintenance-mode-drawer">
        <VerticalGroup>
          Start maintenance mode when performing scheduled maintenance or updates on the infrastructure, which may
          trigger false alarms.
          <GForm form={maintenanceForm} data={initialData} onSubmit={handleSubmit} />
          <HorizontalGroup justify="flex-end">
            <Button variant="secondary" onClick={onHide}>
              Cancel
            </Button>
            <WithPermissionControlTooltip userAction={UserActions.MaintenanceWrite}>
              <Button form={form.name} type="submit" data-testid="create-maintenance-button">
                Start
              </Button>
            </WithPermissionControlTooltip>
          </HorizontalGroup>
        </VerticalGroup>
      </div>
    </Drawer>
  );
});
