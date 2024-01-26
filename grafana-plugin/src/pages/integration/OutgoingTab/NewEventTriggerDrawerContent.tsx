import React, { FC } from 'react';

import { Button, HorizontalGroup, useStyles2, VerticalGroup } from '@grafana/ui';
import { useForm } from 'react-hook-form';

import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { UserActions } from 'utils/authorization';

import { EventTriggerFormFields } from './EventTriggerFormFields';
import { getStyles } from './OutgoingTab.styles';

interface NewEventTriggerDrawerContentProps {
  closeDrawer: () => void;
}

export const NewEventTriggerDrawerContent: FC<NewEventTriggerDrawerContentProps> = ({ closeDrawer }) => {
  const styles = useStyles2(getStyles);
  const { control, handleSubmit } = useForm({ mode: 'all' });

  const onSubmit = () => {};
  return (
    <form onSubmit={handleSubmit(onSubmit)} className={styles.form}>
      <VerticalGroup justify="space-between">
        <div className={styles.formFieldsWrapper}>
          <EventTriggerFormFields control={control} />
        </div>
        <HorizontalGroup justify="flex-end">
          <Button variant="secondary" onClick={closeDrawer}>
            Close
          </Button>
          <WithPermissionControlTooltip userAction={UserActions.OutgoingWebhooksWrite}>
            <Button type="submit">Create</Button>
          </WithPermissionControlTooltip>
        </HorizontalGroup>
      </VerticalGroup>
    </form>
  );
};
