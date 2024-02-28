import React, { FC } from 'react';

import { Button, HorizontalGroup, useStyles2, VerticalGroup } from '@grafana/ui';
import { observer } from 'mobx-react-lite';
import { useForm, FormProvider } from 'react-hook-form';

import { RenderConditionally } from 'components/RenderConditionally/RenderConditionally';
import { Tabs } from 'components/Tabs/Tabs';
import { WebhookLastEventDetails } from 'components/Webhooks/WebhookLastEventDetails';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { useStore } from 'state/useStore';
import { LocationHelper } from 'utils/LocationHelper';
import { UserActions } from 'utils/authorization/authorization';
import { useCommonStyles } from 'utils/hooks';

import { useDrawerWebhook } from './OutgoingTab.hooks';
import { getStyles } from './OutgoingTab.styles';
import { OutgoingTabFormValues, TriggerDetailsQueryStringKey, TriggerDetailsTab } from './OutgoingTab.types';
import { OutgoingWebhookFormFields } from './OutgoingWebhookFormFields';

interface OutgoingWebhookDetailsDrawerTabsProps {
  closeDrawer: () => void;
}
export const OutgoingWebhookDetailsDrawerTabs: FC<OutgoingWebhookDetailsDrawerTabsProps> = ({ closeDrawer }) => {
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
};

interface SettingsProps {
  closeDrawer: () => void;
}
const Settings: FC<SettingsProps> = observer(({ closeDrawer }) => {
  const styles = useStyles2(getStyles);
  const commonStyles = useCommonStyles();
  const webhook = useDrawerWebhook();

  const onSubmit = () => {};

  const form = useForm<OutgoingTabFormValues>({ mode: 'all', defaultValues: webhook });

  return (
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
                <Button type="submit" variant="destructive" fill="outline">
                  Delete
                </Button>
              </WithPermissionControlTooltip>
            </HorizontalGroup>
          </div>
        </VerticalGroup>
      </form>
    </FormProvider>
  );
});

interface LastEventDetailsProps {
  closeDrawer: () => void;
}
const LastEventDetails: FC<LastEventDetailsProps> = observer(({ closeDrawer }) => {
  const commonStyles = useCommonStyles();
  const styles = useStyles2(getStyles);

  const {
    outgoingWebhookStore: { items },
  } = useStore();
  const webhook = items[LocationHelper.getQueryParam(TriggerDetailsQueryStringKey.WebhookId)];

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
