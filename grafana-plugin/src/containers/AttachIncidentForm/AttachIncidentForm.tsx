import React, { useCallback, useState } from 'react';

import { SelectableValue } from '@grafana/data';
import { Button, Field, HorizontalGroup, Icon, Modal } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import moment from 'moment-timezone';

import Text from 'components/Text/Text';
import GSelect from 'containers/GSelect/GSelect';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { Alert } from 'models/alertgroup/alertgroup.types';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization';

import styles from './AttachIncidentForm.module.css';

const cx = cn.bind(styles);

interface AttachIncidentFormProps {
  id: Alert['pk'];
  onUpdate: () => void;
  onHide: () => void;
}

interface GroupedAlertNumberProps {
  value: Alert['pk'];
}

const AttachIncidentForm = observer(({ id, onUpdate, onHide }: AttachIncidentFormProps) => {
  const store = useStore();

  const { alertGroupStore } = store;

  const [selected, setSelected] = useState<Alert['pk']>(undefined);

  const getChangeHandler = useCallback((value) => {
    setSelected(value);
  }, []);

  const handleLinkClick = useCallback(() => {
    alertGroupStore.attachAlert(id, selected).then(() => {
      onHide();
      onUpdate();
    });
  }, [selected, alertGroupStore, id, onHide, onUpdate]);

  const GroupedAlertNumber = observer(({ value }: GroupedAlertNumberProps) => {
    const { alertGroupStore } = useStore();
    const alert = alertGroupStore.items[value];

    return (
      <div>
        #{alert?.inside_organization_number} {alert?.render_for_web?.title}
      </div>
    );
  });

  return (
    <Modal
      isOpen
      icon="link"
      title={
        <HorizontalGroup>
          <Icon size="lg" name="link" />
          <Text.Title level={4}>Attach to another alert group</Text.Title>
        </HorizontalGroup>
      }
      className={cx('root')}
      onDismiss={onHide}
    >
      <Field
        label="Alert group to be attached with"
        description="Linking alert groups together can help the team investigate the underlying issue."
      >
        <WithPermissionControlTooltip userAction={UserActions.AlertGroupsWrite}>
          <GSelect
            showSearch
            modelName="alertGroupStore"
            valueField="pk"
            displayField="render_for_web.title"
            placeholder="Select Incident"
            className={cx('select', 'control')}
            filterOptions={(optionId) => optionId !== id}
            value={selected}
            onChange={getChangeHandler}
            getDescription={(item: Alert) => moment(item.started_at).format('MMM DD, YYYY hh:mm')}
            getOptionLabel={(item: SelectableValue) => <GroupedAlertNumber value={item.value} />}
          />
        </WithPermissionControlTooltip>
      </Field>
      <HorizontalGroup>
        <Button onClick={onHide} variant="secondary">
          Cancel
        </Button>
        <Button onClick={handleLinkClick} variant="primary" disabled={!selected}>
          Attach
        </Button>
      </HorizontalGroup>
    </Modal>
  );
});

export default AttachIncidentForm;
