import React, { useCallback, useState } from 'react';

import { SelectableValue } from '@grafana/data';
import { Button, Field, HorizontalGroup, Icon, Modal } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import moment from 'moment';
import Emoji from 'react-emoji-render';

import Text from 'components/Text/Text';
import GSelect from 'containers/GSelect/GSelect';
import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { AlertGroupStore } from 'models/alertgroup/alertgroup';
import { Alert } from 'models/alertgroup/alertgroup.types';
import { useStore } from 'state/useStore';
import { UserAction } from 'state/userAction';

import styles from './AttachIncidentForm.module.css';

const cx = cn.bind(styles);

interface AttachIncidentFormProps {
  id: Alert['pk'];
  onUpdate: () => void;
  onHide: () => void;
}

const AttachIncidentForm = observer((props: AttachIncidentFormProps) => {
  const { id, onUpdate, onHide } = props;

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
  }, [selected]);

  interface GroupedAlertNumberProps {
    value: Alert['pk'];
  }

  const GroupedAlertNumber = observer((props: GroupedAlertNumberProps) => {
    const store = useStore();
    const { value } = props;

    const { alertGroupStore } = store;
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
          <Text.Title level={4}>Attach to another incident</Text.Title>
        </HorizontalGroup>
      }
      className={cx('root')}
      onDismiss={onHide}
    >
      <Field
        label="Incident to be attached with"
        description="Linking incidents together can help the team investigate the underlying issue."
      >
        <WithPermissionControl userAction={UserAction.UpdateIncidents}>
          <GSelect
            showSearch
            modelName="alertGroupStore"
            valueField="pk"
            displayField="render_for_web.title"
            placeholder="Select Incident"
            className={cx('select', 'control')}
            filterOptions={id => id !== props.id}
            value={selected}
            onChange={getChangeHandler}
            getDescription={(item: Alert) => moment(item.started_at).format('MMM DD, YYYY hh:mm A')}
            getOptionLabel={(item: SelectableValue) => <GroupedAlertNumber value={item.value} />}
          />
        </WithPermissionControl>
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
