import React, { FC, useEffect } from 'react';

import { Button, HorizontalGroup, useStyles2, VerticalGroup } from '@grafana/ui';
import { useForm, FormProvider } from 'react-hook-form';

import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { UserActions } from 'utils/authorization';
import { useCommonStyles } from 'utils/hooks';

import { EventTriggerFormFields } from './EventTriggerFormFields';
import { getStyles } from './OutgoingTab.styles';
import { FormValues } from './OutgoingTab.types';

interface NewEventTriggerDrawerContentProps {
  closeDrawer: () => void;
}

export const NewEventTriggerDrawerContent: FC<NewEventTriggerDrawerContentProps> = ({ closeDrawer }) => {
  const styles = useStyles2(getStyles);
  const commonStyles = useCommonStyles();
  const formMethods = useForm<FormValues>({ mode: 'all' });

  const onSubmit = () => {};
  return (
    <FormProvider {...formMethods}>
      <form onSubmit={formMethods.handleSubmit(onSubmit)} className={styles.form}>
        <VerticalGroup justify="space-between">
          <div className={styles.formFieldsWrapper}>
            <EventTriggerFormFields webhookId="new" />
          </div>
          <div className={commonStyles.bottomDrawerButtons}>
            <HorizontalGroup justify="flex-end">
              <Button variant="secondary" onClick={closeDrawer}>
                Close
              </Button>
              <WithPermissionControlTooltip userAction={UserActions.OutgoingWebhooksWrite}>
                <Button type="submit">Create</Button>
              </WithPermissionControlTooltip>
            </HorizontalGroup>
          </div>
        </VerticalGroup>
      </form>
    </FormProvider>
  );
};
