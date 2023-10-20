import React, { FC, useCallback, useContext } from 'react';

import { Button, Drawer, HorizontalGroup, VerticalGroup } from '@grafana/ui';

import GForm from 'components/GForm/GForm';
import AddResponders from 'containers/AddResponders/AddResponders';
import { prepareForUpdate } from 'containers/AddResponders/AddResponders.helpers';
import { AlertReceiveChannelStore } from 'models/alert_receive_channel/alert_receive_channel';
import { Alert as AlertType } from 'models/alertgroup/alertgroup.types';
import { DirectPagingContext } from 'state/context/directPaging';
import { useStore } from 'state/useStore';
import { openWarningNotification } from 'utils';

import { manualAlertFormConfig, FormData } from './ManualAlertGroup.config';

interface ManualAlertGroupProps {
  onHide: () => void;
  onCreate: (id: AlertType['pk']) => void;
  alertReceiveChannelStore: AlertReceiveChannelStore;
}

const data: FormData = {
  message: '',
};

const ManualAlertGroup: FC<ManualAlertGroupProps> = ({ onCreate, onHide }) => {
  const { directPagingStore } = useStore();

  const { selectedTeamResponder, selectedUserResponders, resetSelectedUsers, resetSelectedTeam } =
    useContext(DirectPagingContext);

  const onHideDrawer = useCallback(() => {
    resetSelectedUsers();
    resetSelectedTeam();
    onHide();
  }, [resetSelectedUsers, resetSelectedTeam, onHide]);

  const hasSelectedEitherATeamOrAUser = selectedTeamResponder !== undefined || selectedUserResponders.length > 0;

  // TODO: add a loading state while we're waiting to hear back from the API when submitting
  // const [directPagingLoading, setdirectPagingLoading] = useState<boolean>();

  const handleFormSubmit = useCallback(
    async (data: FormData) => {
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
        <GForm form={manualAlertFormConfig} data={data} onSubmit={handleFormSubmit} />
        <AddResponders mode="create" />
        <HorizontalGroup justify="flex-end">
          <Button variant="secondary" onClick={onHideDrawer}>
            Cancel
          </Button>
          {/* TODO: make the button be disabled if the form is not valid */}
          <Button type="submit" form={manualAlertFormConfig.name} disabled={!hasSelectedEitherATeamOrAUser}>
            Create
          </Button>
        </HorizontalGroup>
      </VerticalGroup>
    </Drawer>
  );
};

export default ManualAlertGroup;
