import React, { FC, useCallback } from 'react';

import { Button, Drawer, Field, HorizontalGroup, TextArea, useStyles2, VerticalGroup } from '@grafana/ui';
import { observer } from 'mobx-react';
import { Controller, FormProvider, useForm } from 'react-hook-form';
import { getUtilStyles } from 'styles/utils.styles';

import { AddResponders } from 'containers/AddResponders/AddResponders';
import { prepareForUpdate } from 'containers/AddResponders/AddResponders.helpers';
import { AlertReceiveChannelStore } from 'models/alert_receive_channel/alert_receive_channel';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useStore } from 'state/useStore';
import { openWarningNotification } from 'utils/utils';

export type FormData = {
  message: string;
};

interface ManualAlertGroupProps {
  onHide: () => void;
  onCreate: (id: ApiSchemas['AlertGroup']['pk']) => void;
  alertReceiveChannelStore: AlertReceiveChannelStore;
}

export const ManualAlertGroup: FC<ManualAlertGroupProps> = observer(({ onCreate, onHide }) => {
  const { directPagingStore } = useStore();
  const { selectedTeamResponder, selectedUserResponders } = directPagingStore;

  const onHideDrawer = useCallback(() => {
    directPagingStore.resetSelectedUsers();
    directPagingStore.resetSelectedTeam();
    onHide();
  }, [onHide]);

  const formMethods = useForm<FormData>({
    mode: 'onChange',
    defaultValues: { message: '' },
  });

  const {
    handleSubmit,
    control,
    formState: { errors },
  } = formMethods;

  const formIsSubmittable = selectedTeamResponder !== null || selectedUserResponders.length > 0;

  // TODO: add a loading state while we're waiting to hear back from the API when submitting
  // const [directPagingLoading, setdirectPagingLoading] = useState<boolean>();

  const onSubmit = async (data: FormData) => {
    const transformedData = prepareForUpdate(selectedUserResponders, selectedTeamResponder, data);

    const resp = await directPagingStore.createManualAlertRule(transformedData);

    if (!resp) {
      openWarningNotification('There was an issue creating the alert group, please try again');
      return;
    }

    directPagingStore.resetSelectedUsers();
    directPagingStore.resetSelectedTeam();

    onCreate(resp.alert_group_id);
    onHide();
  };

  const utils = useStyles2(getUtilStyles);

  return (
    <Drawer scrollableContent title="New escalation" onClose={onHideDrawer} closeOnMaskClick={false} width="70%">
      <VerticalGroup>
        <FormProvider {...formMethods}>
          <form id="Manual Alert Group" onSubmit={handleSubmit(onSubmit)} className={utils.width100}>
            <Controller
              name="message"
              control={control}
              rules={{ required: 'Message is required' }}
              render={({ field }) => (
                <Field label="What is going on?" invalid={Boolean(errors.message)} error={errors.message?.message}>
                  <TextArea name="message" rows={4} {...field} />
                </Field>
              )}
            />
            <AddResponders mode="create" />
            <div className="buttons">
              <HorizontalGroup justify="flex-end">
                <Button variant="secondary" onClick={onHideDrawer}>
                  Cancel
                </Button>
                <Button type="submit" disabled={!formIsSubmittable}>
                  Create
                </Button>
              </HorizontalGroup>
            </div>
          </form>
        </FormProvider>
      </VerticalGroup>
    </Drawer>
  );
});
