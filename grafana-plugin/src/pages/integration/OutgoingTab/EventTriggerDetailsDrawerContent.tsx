import React, { FC, useMemo } from 'react';

import { Button, HorizontalGroup, useStyles2, VerticalGroup } from '@grafana/ui';
import { useForm, FormProvider } from 'react-hook-form';

import Tabs from 'components/Tabs/Tabs';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import LocationHelper from 'utils/LocationHelper';
import { UserActions } from 'utils/authorization';

import { EventTriggerFormFields } from './EventTriggerFormFields';
import { getStyles } from './OutgoingTab.styles';
import { TriggerDetailsQueryStringKey, TriggerDetailsTab, FormValues } from './OutgoingTab.types';
import { useStore } from 'state/useStore';
import { getEventDetailsRows } from './EventTriggerDetailsDrawerContent.utils';
import WebhookLastEventDetails from 'components/Webhooks/WebhookLastEventDetails';
import { observer } from 'mobx-react-lite';

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
          <div className={styles.bottomButtons}>
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
  const styles = useStyles2(getStyles);

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
      <div className={styles.bottomButtons}>
        <HorizontalGroup justify="flex-end">
          <Button variant="secondary" onClick={closeDrawer}>
            Close
          </Button>
        </HorizontalGroup>
      </div>
    </div>
  );
});
