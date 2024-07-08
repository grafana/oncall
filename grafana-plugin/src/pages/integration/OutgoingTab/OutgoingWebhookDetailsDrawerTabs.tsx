import React, { FC } from 'react';

import { Button, ConfirmModal, HorizontalGroup, useStyles2, VerticalGroup } from '@grafana/ui';
import { observer } from 'mobx-react';
import { useForm, FormProvider } from 'react-hook-form';

import { RenderConditionally } from 'components/RenderConditionally/RenderConditionally';
import { Tabs } from 'components/Tabs/Tabs';
import { WebhookLastEventDetails } from 'components/Webhooks/WebhookLastEventDetails';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization/authorization';
import { useCommonStyles, useConfirmModal } from 'utils/hooks';

import { useDrawerWebhook, useIntegrationIdFromUrl } from './OutgoingTab.hooks';
import { getStyles } from './OutgoingTab.styles';
import { OutgoingTabFormValues, TriggerDetailsQueryStringKey, TriggerDetailsTab } from './OutgoingTab.types';
import { OutgoingWebhookFormFields } from './OutgoingWebhookFormFields';

interface OutgoingWebhookDetailsDrawerTabsProps {
  closeDrawer: () => void;
}
export const OutgoingWebhookDetailsDrawerTabs: FC<OutgoingWebhookDetailsDrawerTabsProps> = observer(
  ({ closeDrawer }) => {
    const styles = useStyles2(getStyles);
    const webhook = useDrawerWebhook();

    return (
      <RenderConditionally shouldRender={Boolean(webhook)}>
        <div className={styles.tabsWrapper}>
          <Tabs
            queryStringKey={TriggerDetailsQueryStringKey.ActiveTab}
            tabs={[
              { label: TriggerDetailsTab.Settings, content: <Settings closeDrawer={closeDrawer} /> },
              { label: TriggerDetailsTab.LastEvent, content: <LastEventDetails closeDrawer={closeDrawer} /> },
            ]}
          />
        </div>
      </RenderConditionally>
    );
  }
);

interface SettingsProps {
  closeDrawer: () => void;
}
const Settings: FC<SettingsProps> = observer(({ closeDrawer }) => {
  const { alertReceiveChannelWebhooksStore } = useStore();
  const styles = useStyles2(getStyles);
  const commonStyles = useCommonStyles();
  const webhook = useDrawerWebhook();
  const integrationId = useIntegrationIdFromUrl();
  const { modalProps, openModal } = useConfirmModal();

  const onSubmit = async (values: OutgoingTabFormValues) => {
    if (!values.triggerTemplateToogle) {
      values.trigger_template = null;
    }
    await alertReceiveChannelWebhooksStore.update(integrationId, { id: webhook.id, ...values });
    closeDrawer();
  };

  const onDelete = () => {
    openModal({
      confirmText: 'Delete',
      onConfirm: async () => {
        closeDrawer();
        await alertReceiveChannelWebhooksStore.delete(integrationId, webhook.id);
      },
      title: `Are you sure you want to delete outgoing webhook?`,
    });
  };

  const form = useForm<OutgoingTabFormValues>({
    mode: 'all',
    defaultValues: { ...webhook, triggerTemplateToogle: Boolean(webhook.trigger_template) },
  });

  return (
    <>
      <ConfirmModal {...modalProps} />
      <FormProvider {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className={styles.form}>
          <VerticalGroup justify="space-between">
            <div className={styles.formFieldsWrapper}>
              <OutgoingWebhookFormFields webhookId={webhook.id} />
            </div>
            <div className={commonStyles.bottomDrawerButtons}>
              <HorizontalGroup justify="flex-end">
                <Button variant="secondary" onClick={closeDrawer}>
                  Close
                </Button>
                <WithPermissionControlTooltip userAction={UserActions.OutgoingWebhooksWrite}>
                  <Button
                    type="submit"
                    onClick={() => {
                      form.handleSubmit(onSubmit);
                    }}
                  >
                    Update
                  </Button>
                </WithPermissionControlTooltip>
                <WithPermissionControlTooltip userAction={UserActions.OutgoingWebhooksWrite}>
                  <Button variant="destructive" fill="outline" onClick={onDelete}>
                    Delete
                  </Button>
                </WithPermissionControlTooltip>
              </HorizontalGroup>
            </div>
          </VerticalGroup>
        </form>
      </FormProvider>
    </>
  );
});

interface LastEventDetailsProps {
  closeDrawer: () => void;
}
const LastEventDetails: FC<LastEventDetailsProps> = observer(({ closeDrawer }) => {
  const commonStyles = useCommonStyles();
  const styles = useStyles2(getStyles);
  const webhook = useDrawerWebhook();

  if (!webhook) {
    return null;
  }

  return (
    <div>
      <WebhookLastEventDetails webhook={webhook} sourceCodeRootClassName={styles.sourceCodeRoot} />
      <div className={commonStyles.bottomDrawerButtons}>
        <HorizontalGroup justify="flex-end">
          <Button variant="secondary" onClick={closeDrawer}>
            Close
          </Button>
        </HorizontalGroup>
      </div>
    </div>
  );
});
