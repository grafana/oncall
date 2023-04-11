import React, { useCallback } from 'react';

import { Button, Drawer, HorizontalGroup, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import GForm from 'components/GForm/GForm';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { MaintenanceType } from 'models/maintenance/maintenance.types';
import { useStore } from 'state/useStore';
import { showApiError } from 'utils';
import { UserActions } from 'utils/authorization';

import { form } from './MaintenanceForm.config';

import styles from './MaintenanceForm.module.css';

const cx = cn.bind(styles);

interface MaintenanceFormProps {
  initialData: {
    type?: MaintenanceType;
    alert_receive_channel_id?: AlertReceiveChannel['id'];
  };
  onHide: () => void;
  onUpdate: () => void;
}

const MaintenanceForm = observer((props: MaintenanceFormProps) => {
  const { onUpdate, onHide, initialData = {} } = props;

  const store = useStore();

  const { maintenanceStore } = store;

  const handleSubmit = useCallback((data) => {
    maintenanceStore
      .startMaintenanceMode(
        MaintenanceType.alert_receive_channel,
        data.mode,
        data.duration,
        data.alert_receive_channel_id
      )
      .then(() => {
        onHide();

        onUpdate();
      })
      .catch(showApiError);
  }, []);

  return (
    <Drawer scrollableContent title="Start Maintenance Mode" onClose={onHide} closeOnMaskClick={false}>
      <div className={cx('content')}>
        <VerticalGroup>
          <GForm form={form} data={initialData} onSubmit={handleSubmit} />
          <HorizontalGroup justify="flex-end">
            <Button variant="secondary" onClick={onHide}>
              Cancel
            </Button>
            <WithPermissionControlTooltip userAction={UserActions.MaintenanceWrite}>
              <Button form={form.name} type="submit">
                Start
              </Button>
            </WithPermissionControlTooltip>
          </HorizontalGroup>
        </VerticalGroup>
      </div>
    </Drawer>
  );
});

export default MaintenanceForm;
