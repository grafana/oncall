import React, { useCallback, useState } from 'react';

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

import styles from './EditTeamForm.module.css';

const cx = cn.bind(styles);

interface EditTeamFormProps {
  // id: Alert['pk'];
  // onUpdate: () => void;
  // onHide: () => void;
}
//EscalationChainForm

const EditTeamForm = observer(({ id, onUpdate, onHide }: EditTeamFormProps) => {
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

  return (
    <Modal
      isOpen
      icon="link"
      title={
        <HorizontalGroup>
          <Icon size="lg" name="link" />
          <Text.Title level={4}>Edit team</Text.Title>
        </HorizontalGroup>
      }
      className={cx('root')}
      onDismiss={onHide}
    >
      <Field
        label="Incident to be attached with"
        description="Linking incidents together can help the team investigate the underlying issue."
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
            getDescription={(item: Alert) => moment(item.started_at).format('MMM DD, YYYY hh:mm A')}
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

export default EditTeamForm;
