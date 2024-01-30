import React, { useEffect } from 'react';

import { IconButton, HorizontalGroup, Icon, ConfirmModal } from '@grafana/ui';
import { observer } from 'mobx-react-lite';
import CopyToClipboard from 'react-copy-to-clipboard';

import GTable from 'components/GTable/GTable';
import HamburgerContextMenu from 'components/HamburgerContextMenu/HamburgerContextMenu';
import Text from 'components/Text/Text';
import { WebhookLastEventTimestamp } from 'components/Webhooks/WebhookLastEventTimestamp';
import { OutgoingWebhook } from 'models/outgoing_webhook/outgoing_webhook.types';
import { useStore } from 'state/useStore';
import { openNotification } from 'utils';
import LocationHelper from 'utils/LocationHelper';
import { UserActions } from 'utils/authorization';
import { useConfirmModal } from 'utils/hooks';

import { OutgoingTabDrawerKey, TriggerDetailsQueryStringKey, TriggerDetailsTab } from './OutgoingTab.types';

export const EventTriggersTable = observer(({ openDrawer }: { openDrawer: (key: OutgoingTabDrawerKey) => void }) => {
  const {
    outgoingWebhookStore: { getSearchResult, updateItems },
  } = useStore();

  useEffect(() => {
    updateItems();
  }, []);

  const openTriggerDetailsDrawer = (tab: TriggerDetailsTab, webhookId: string) => {
    LocationHelper.update(
      { [TriggerDetailsQueryStringKey.ActiveTab]: tab, [TriggerDetailsQueryStringKey.WebhookId]: webhookId },
      'partial'
    );
    openDrawer('triggerDetails');
  };

  const webhooks = getSearchResult();

  return (
    <GTable
      emptyText={webhooks ? 'No outgoing webhooks found' : 'Loading...'}
      rowKey="id"
      columns={getColumns(openTriggerDetailsDrawer)}
      data={webhooks}
    />
  );
});

const getColumns = (openTriggerDetailsDrawer: (tab: TriggerDetailsTab, webhookId: string) => void) => [
  {
    width: '35%',
    title: 'Event Trigger',
    dataIndex: 'trigger_type_name',
    render: (triggerType: string) => <>{triggerType}</>,
  },
  {
    width: '65%',
    title: 'Last event',
    render: (webhook: OutgoingWebhook) => (
      <WebhookLastEventTimestamp
        webhook={webhook}
        openDrawer={() => openTriggerDetailsDrawer(TriggerDetailsTab.LastEvent, webhook.id)}
      />
    ),
  },
  {
    key: 'action',
    render: (webhook: OutgoingWebhook) => (
      <EventTriggerContextMenu webhook={webhook} openDrawer={openTriggerDetailsDrawer} />
    ),
  },
];

const EventTriggerContextMenu = ({
  webhook,
  openDrawer,
}: {
  webhook: OutgoingWebhook;
  openDrawer: (tab: TriggerDetailsTab, webhookId: string) => void;
}) => {
  const { modalProps, openModal } = useConfirmModal();

  return (
    <>
      <ConfirmModal {...modalProps} />
      <HamburgerContextMenu
        items={[
          {
            onClick: () => {
              openDrawer(TriggerDetailsTab.LastEvent, webhook.id);
            },
            requiredPermission: UserActions.OutgoingWebhooksRead,
            label: <Text type="primary">View Last Run</Text>,
          },
          {
            onClick: () => {
              openDrawer(TriggerDetailsTab.Settings, webhook.id);
            },
            requiredPermission: UserActions.OutgoingWebhooksWrite,
            label: <Text type="primary">Edit settings</Text>,
          },
          {
            onClick: () => {
              openModal({
                onConfirm: () => {
                  console.log('TODO: disable webhook');
                },
                title: `Are you sure you want to ${webhook.is_webhook_enabled ? 'disable' : 'enable'} event trigger?`,
              });
            },
            requiredPermission: UserActions.OutgoingWebhooksWrite,
            label: <Text type="primary">{webhook.is_webhook_enabled ? 'Disable' : 'Enable'}</Text>,
          },
          {
            label: (
              <CopyToClipboard
                key="uid"
                text={webhook.id}
                onCopy={() => openNotification('Webhook ID has been copied')}
              >
                <div>
                  <HorizontalGroup type="primary" spacing="xs">
                    <Icon name="clipboard-alt" />
                    <Text type="primary">UID: {webhook.id}</Text>
                  </HorizontalGroup>
                </div>
              </CopyToClipboard>
            ),
          },
          'divider',
          {
            onClick: () => {
              openModal({
                onConfirm: () => {
                  console.log('TODO: delete webhook');
                },
                title: `Are you sure you want to delete event trigger?`,
              });
            },
            requiredPermission: UserActions.OutgoingWebhooksWrite,
            label: (
              <HorizontalGroup spacing="xs">
                <IconButton tooltip="Remove" tooltipPlacement="top" variant="destructive" name="trash-alt" />
                <Text type="danger">Delete</Text>
              </HorizontalGroup>
            ),
          },
        ]}
      />
    </>
  );
};
