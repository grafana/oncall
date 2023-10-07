import React, { FC, useCallback, useContext } from 'react';

import { Button, Drawer, HorizontalGroup, VerticalGroup } from '@grafana/ui';

import GForm from 'components/GForm/GForm';
import EscalationVariants from 'containers/EscalationVariants/EscalationVariants';
import { prepareForUpdate } from 'containers/EscalationVariants/EscalationVariants.helpers';
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

  const { selectedTeamResponder, selectedUserResponders } = useContext(DirectPagingContext);

  const hasSelectedEitherATeamOrAUser = selectedTeamResponder !== undefined || selectedUserResponders.length > 0;

  // TODO: add a loading state while we're waiting to hear back from the API when submitting
  // const [directPagingLoading, setdirectPagingLoading] = useState<boolean>();

  // const [chatOpsAvailableChannels, setChatopsAvailableChannels] = useState<any>();

  const handleFormSubmit = useCallback(
    async (data: FormData) => {
      console.log('SUBMITTING FORM', data);

      const transformedData = prepareForUpdate(selectedTeamResponder, selectedUserResponders, data);
      console.log('TRANSFORMED DATA IS', transformedData);

      const resp = await directPagingStore.createManualAlertRule(transformedData);

      if (!resp) {
        openWarningNotification('There was an issue creating the alert group, please try again');
        return;
      }

      onCreate(resp.alert_group_id);
      onHide();
    },
    [prepareForUpdate, selectedTeamResponder, selectedUserResponders]
  );

  return (
    <Drawer scrollableContent title="New escalation" onClose={onHide} closeOnMaskClick={false} width="70%">
      <VerticalGroup>
        {/* TODO: pass in generic form data here */}
        <GForm form={manualAlertFormConfig} data={data} onSubmit={handleFormSubmit} />
        <EscalationVariants mode="create" />
        <HorizontalGroup justify="flex-end">
          <Button variant="secondary" onClick={onHide}>
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
