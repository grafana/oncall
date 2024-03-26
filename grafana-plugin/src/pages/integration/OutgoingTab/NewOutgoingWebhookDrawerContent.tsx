import React, { FC } from 'react';

import { Button, HorizontalGroup, useStyles2 } from '@grafana/ui';
import { useForm, FormProvider } from 'react-hook-form';

import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization/authorization';
import { useCommonStyles } from 'utils/hooks';

import { useIntegrationIdFromUrl } from './OutgoingTab.hooks';
import { getStyles } from './OutgoingTab.styles';
import { OutgoingTabFormValues } from './OutgoingTab.types';
import { OutgoingWebhookFormFields } from './OutgoingWebhookFormFields';

interface NewOutgoingWebhookDrawerContentProps {
  closeDrawer: () => void;
}

export const NewOutgoingWebhookDrawerContent: FC<NewOutgoingWebhookDrawerContentProps> = ({ closeDrawer }) => {
  const { alertReceiveChannelWebhooksStore } = useStore();
  const styles = useStyles2(getStyles);
  const commonStyles = useCommonStyles();
  const formMethods = useForm<OutgoingTabFormValues>({
    mode: 'onChange',
    defaultValues: { is_webhook_enabled: false },
  });
  const integrationId = useIntegrationIdFromUrl();

  const onSubmit = async (values: OutgoingTabFormValues) => {
    if (!values.triggerTemplateToogle) {
      values.trigger_template = null;
    }
    await alertReceiveChannelWebhooksStore.create(integrationId, { ...values, name: `${new Date().getTime()}` });
    closeDrawer();
  };

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
