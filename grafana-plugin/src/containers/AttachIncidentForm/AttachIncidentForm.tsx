import React, { useCallback, useState } from 'react';

import { css, cx } from '@emotion/css';
import { SelectableValue } from '@grafana/data';
import { Button, Field, Icon, Modal, Stack } from '@grafana/ui';
import { UserActions } from 'helpers/authorization/authorization';
import { observer } from 'mobx-react';
import moment from 'moment-timezone';

import { Text } from 'components/Text/Text';
import { GSelect } from 'containers/GSelect/GSelect';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { AlertGroupHelper } from 'models/alertgroup/alertgroup.helpers';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useStore } from 'state/useStore';

interface AttachIncidentFormProps {
  id: ApiSchemas['AlertGroup']['pk'];
  onUpdate: () => void;
  onHide: () => void;
}

interface GroupedAlertNumberProps {
  value: ApiSchemas['AlertGroup']['pk'];
}

const GroupedAlertNumber = observer(({ value }: GroupedAlertNumberProps) => {
  const { alertGroupStore } = useStore();
  const alert = alertGroupStore.alerts.get(value);

  return (
    <div>
      #{alert?.inside_organization_number} {alert?.render_for_web?.title}
    </div>
  );
});

export const AttachIncidentForm = observer(({ id, onUpdate, onHide }: AttachIncidentFormProps) => {
  const store = useStore();

  const {
    alertGroupStore,
    // dereferencing alerts is needed to rerender GSelect
    alertGroupStore: { alerts: alertGroupAlerts },
  } = store;

  const [selected, setSelected] = useState<ApiSchemas['AlertGroup']['pk']>(undefined);

  const getChangeHandler = useCallback((value) => {
    setSelected(value);
  }, []);

  const handleLinkClick = useCallback(async () => {
    await AlertGroupHelper.attachAlert(id, selected);
    onHide();
    onUpdate();
  }, [selected, alertGroupStore, id, onHide, onUpdate]);

  return (
    <Modal
      isOpen
      icon="link"
      title={
        <Stack>
          <Icon size="lg" name="link" />
          <Text.Title level={4}>Attach to another alert group</Text.Title>
        </Stack>
      }
      className={css`
        display: block;
      `}
      onDismiss={onHide}
    >
      <Field
        label="Alert group to be attached with"
        description="Linking alert groups together can help the team investigate the underlying issue."
      >
        <WithPermissionControlTooltip userAction={UserActions.AlertGroupsWrite}>
          <GSelect<ApiSchemas['AlertGroup']>
            items={Object.fromEntries(alertGroupAlerts)}
            fetchItemsFn={async (query: string) => {
              await alertGroupStore.fetchAlertGroups(false, query);
            }}
            fetchItemFn={alertGroupStore.getAlert}
            getSearchResult={() => AlertGroupHelper.getAlertSearchResult(alertGroupStore).results}
            valueField="pk"
            displayField="render_for_web.title"
            placeholder="Select Alert Group"
            className={cx('select', 'control')}
            filterOptions={(optionId) => optionId !== id}
            value={selected}
            onChange={getChangeHandler}
            getDescription={(item: ApiSchemas['AlertGroup']) => moment(item.started_at).format('MMM DD, YYYY hh:mm')}
            getOptionLabel={(item: SelectableValue) => <GroupedAlertNumber value={item.value} />}
          />
        </WithPermissionControlTooltip>
      </Field>
      <Stack>
        <Button onClick={onHide} variant="secondary">
          Cancel
        </Button>
        <Button onClick={handleLinkClick} variant="primary" disabled={!selected}>
          Attach
        </Button>
      </Stack>
    </Modal>
  );
});
