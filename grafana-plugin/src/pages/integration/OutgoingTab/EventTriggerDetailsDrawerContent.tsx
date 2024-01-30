import React, { FC } from 'react';

import { Button, HorizontalGroup, useStyles2, VerticalGroup } from '@grafana/ui';
import { observer } from 'mobx-react-lite';
import { useForm, FormProvider } from 'react-hook-form';

import Tabs from 'components/Tabs/Tabs';
import WebhookLastEventDetails from 'components/Webhooks/WebhookLastEventDetails';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { useStore } from 'state/useStore';
import LocationHelper from 'utils/LocationHelper';
import { UserActions } from 'utils/authorization';
import { useCommonStyles } from 'utils/hooks';

import { EventTriggerFormFields } from './EventTriggerFormFields';
import { getStyles } from './OutgoingTab.styles';
import { TriggerDetailsQueryStringKey, TriggerDetailsTab, FormValues } from './OutgoingTab.types';

interface EventTriggerDetailsDrawerContentProps {
  closeDrawer: () => void;
}
export const EventTriggerDetailsDrawerContent: FC<EventTriggerDetailsDrawerContentProps> = ({ closeDrawer }) => {
  return (
    <Tabs
      queryStringKey={TriggerDetailsQueryStringKey.ActiveTab}
      tabs={[
        { label: TriggerDetailsTab.Settings, content: <Settings closeDrawer={closeDrawer} /> },
        { label: TriggerDetailsTab.LastEvent, content: <LastEventDetails closeDrawer={closeDrawer} /> },
      ]}
    />
  );
};

interface SettingsProps {
  closeDrawer: () => void;
}
const Settings: FC<SettingsProps> = ({ closeDrawer }) => {
  const styles = useStyles2(getStyles);
  const commonStyles = useCommonStyles();
  const formMethods = useForm<FormValues>({ mode: 'all' });
  const webhookId = LocationHelper.getQueryParam(TriggerDetailsQueryStringKey.WebhookId);

  const onSubmit = () => {};

  return (
    <FormProvider {...formMethods}>
      <form onSubmit={formMethods.handleSubmit(onSubmit)} className={styles.form}>
        <VerticalGroup justify="space-between">
          <div className={styles.formFieldsWrapper}>
            <EventTriggerFormFields webhookId={webhookId} />
          </div>
          <div className={commonStyles.bottomDrawerButtons}>
            <HorizontalGroup justify="flex-end">
              <Button variant="secondary" onClick={closeDrawer}>
                Close
              </Button>
              <WithPermissionControlTooltip userAction={UserActions.OutgoingWebhooksWrite}>
                <Button type="submit" variant="destructive">
                  Delete
                </Button>
              </WithPermissionControlTooltip>
              <WithPermissionControlTooltip userAction={UserActions.OutgoingWebhooksWrite}>
                <Button type="submit">Update</Button>
              </WithPermissionControlTooltip>
            </HorizontalGroup>
          </div>
        </VerticalGroup>
      </form>
    </FormProvider>
  );
};

interface LastEventDetailsProps {
  closeDrawer: () => void;
}
const LastEventDetails: FC<LastEventDetailsProps> = observer(({ closeDrawer }) => {
  const commonStyles = useCommonStyles();

  const {
    outgoingWebhookStore: { items },
  } = useStore();
  const webhook = items[LocationHelper.getQueryParam(TriggerDetailsQueryStringKey.WebhookId)];

  const onSubmit = () => {};

  if (!webhook) {
    return null;
  }

  return (
    <div>
      <WebhookLastEventDetails webhook={webhook} />
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
