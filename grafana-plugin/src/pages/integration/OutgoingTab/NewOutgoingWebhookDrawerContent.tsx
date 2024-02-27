import React, { FC } from 'react';

import { Button, HorizontalGroup, useStyles2, VerticalGroup } from '@grafana/ui';
import { useForm, FormProvider } from 'react-hook-form';

import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { UserActions } from 'utils/authorization/authorization';
import { useCommonStyles } from 'utils/hooks';

import { getStyles } from './OutgoingTab.styles';
import { OutgoingTabFormValues } from './OutgoingTab.types';
import { OutgoingWebhookFormFields } from './OutgoingWebhookFormFields';

interface NewOutgoingWebhookDrawerContentProps {
  closeDrawer: () => void;
}

export const NewOutgoingWebhookDrawerContent: FC<NewOutgoingWebhookDrawerContentProps> = ({ closeDrawer }) => {
  const styles = useStyles2(getStyles);
  const commonStyles = useCommonStyles();
  const formMethods = useForm<OutgoingTabFormValues>({ mode: 'all' });

  const onSubmit = () => {};

  return (
    <FormProvider {...formMethods}>
      <form onSubmit={formMethods.handleSubmit(onSubmit)} className={styles.form}>
        <div className={styles.formFieldsWrapper}>
          <OutgoingWebhookFormFields webhookId="new" />
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
      </form>
    </FormProvider>
  );
};
