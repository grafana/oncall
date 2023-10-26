import React, { FC, useCallback, useContext, useState } from 'react';

import { Button, Drawer, HorizontalGroup, VerticalGroup } from '@grafana/ui';

import GForm from 'components/GForm/GForm';
import AddResponders from 'containers/AddResponders/AddResponders';
import { prepareForUpdate } from 'containers/AddResponders/AddResponders.helpers';
import { AlertReceiveChannelStore } from 'models/alert_receive_channel/alert_receive_channel';
import { Alert as AlertType } from 'models/alertgroup/alertgroup.types';
import { DirectPagingContext } from 'state/context/directPaging';
import { useStore } from 'state/useStore';
import { openWarningNotification } from 'utils';

import { manualAlertFormConfig, ManualAlertGroupFormData } from './ManualAlertGroup.config';

interface ManualAlertGroupProps {
  onHide: () => void;
  onCreate: (id: AlertType['pk']) => void;
  alertReceiveChannelStore: AlertReceiveChannelStore;
}

const data: ManualAlertGroupFormData = {
  message: '',
};

const ManualAlertGroup: FC<ManualAlertGroupProps> = ({ onCreate, onHide }) => {
  const { directPagingStore } = useStore();

  const [formIsValid, setFormIsValid] = useState<boolean>(false);
  const { selectedTeamResponder, selectedUserResponders, resetSelectedUsers, resetSelectedTeam } =
    useContext(DirectPagingContext);

  const onHideDrawer = useCallback(() => {
    resetSelectedUsers();
    resetSelectedTeam();
    onHide();
  }, [resetSelectedUsers, resetSelectedTeam, onHide]);

  const hasSelectedEitherATeamOrAUser = selectedTeamResponder !== null || selectedUserResponders.length > 0;
  const formIsSubmittable = hasSelectedEitherATeamOrAUser && formIsValid;

  // TODO: add a loading state while we're waiting to hear back from the API when submitting
  // const [directPagingLoading, setdirectPagingLoading] = useState<boolean>();

  const handleFormSubmit = useCallback(
    async (data: ManualAlertGroupFormData) => {
      const transformedData = prepareForUpdate(selectedUserResponders, selectedTeamResponder, data);

      const resp = await directPagingStore.createManualAlertRule(transformedData);

      if (!resp) {
        openWarningNotification('There was an issue creating the alert group, please try again');
        return;
      }

      resetSelectedUsers();
      resetSelectedTeam();

      onCreate(resp.alert_group_id);
      onHide();
    },
    [prepareForUpdate, selectedTeamResponder, selectedUserResponders, resetSelectedUsers, resetSelectedTeam]
  );

  return (
    <Drawer scrollableContent title="New escalation" onClose={onHideDrawer} closeOnMaskClick={false} width="70%">
      <VerticalGroup>
        <GForm form={manualAlertFormConfig} data={data} onSubmit={handleFormSubmit} onChange={setFormIsValid} />
        <AddResponders mode="create" />
        <HorizontalGroup justify="flex-end">
          <Button variant="secondary" onClick={onHideDrawer}>
            Cancel
          </Button>
          <Button type="submit" form={manualAlertFormConfig.name} disabled={!formIsSubmittable}>
            Create
          </Button>
        </HorizontalGroup>
      </VerticalGroup>
    </Drawer>
  );
};

export default ManualAlertGroup;
