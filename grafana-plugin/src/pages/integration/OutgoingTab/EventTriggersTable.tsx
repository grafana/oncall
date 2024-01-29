import React, { useEffect } from 'react';

import { IconButton, HorizontalGroup, Icon } from '@grafana/ui';
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

import { OutgoingTabDrawerKey, TriggerDetailsQueryStringKey, TriggerDetailsTab } from './OutgoingTab.types';

export const EventTriggersTable = observer(({ openDrawer }: { openDrawer: (key: OutgoingTabDrawerKey) => void }) => {
  const {
    outgoingWebhookStore: { getSearchResult, updateItems },
  } = useStore();

  useEffect(() => {
    updateItems();
  }, []);

  const webhooks = getSearchResult();

  return (
    <GTable
      emptyText={webhooks ? 'No outgoing webhooks found' : 'Loading...'}
      rowKey="id"
      columns={getColumns(openDrawer)}
      data={webhooks}
    />
  );
});

const getColumns = (openDrawer: (key: OutgoingTabDrawerKey) => void) => [
  {
    width: '35%',
    title: 'Event Trigger',
    dataIndex: 'trigger_type_name',
    render: (triggerType: string) => <>{triggerType}</>,
  },
  {
    width: '65%',
    title: 'Last event',
    render: (webhook: OutgoingWebhook) => <WebhookLastEventTimestamp webhook={webhook} openDrawer={openDrawer} />,
  },
  {
    key: 'action',
    render: (webhook: OutgoingWebhook) => <EventTriggerContextMenu webhook={webhook} openDrawer={openDrawer} />,
  },
];

const EventTriggerContextMenu = ({
  webhook,
  openDrawer,
}: {
  webhook: OutgoingWebhook;
  openDrawer: (key: OutgoingTabDrawerKey) => void;
}) => {
  const onOpenDrawer = (tab: TriggerDetailsTab) => {
    LocationHelper.update(
      { [TriggerDetailsQueryStringKey.ActiveTab]: tab, [TriggerDetailsQueryStringKey.WebhookId]: webhook.id },
      'partial'
    );
    openDrawer('triggerDetails');
  };
  return (
    <HamburgerContextMenu
      items={[
        {
          onClick: () => {
            onOpenDrawer(TriggerDetailsTab.LastEvent);
          },
          requiredPermission: UserActions.OutgoingWebhooksRead,
          label: <Text type="primary">View Last Run</Text>,
        },
        {
          onClick: () => {
            onOpenDrawer(TriggerDetailsTab.Settings);
          },
          requiredPermission: UserActions.OutgoingWebhooksWrite,
          label: <Text type="primary">Edit settings</Text>,
        },
        {
          onClick: () => {},
          // this.setState({
          //   confirmationModal: {
          //     isOpen: true,
          //     confirmText: 'Confirm',
          //     dismissText: 'Cancel',
          //     onConfirm: () => this.onDisableWebhook(record.id, !record.is_webhook_enabled),
          //     title: `Are you sure you want to ${record.is_webhook_enabled ? 'disable' : 'enable'} webhook?`,
          //   } as ConfirmModalProps,
          // }),
          requiredPermission: UserActions.OutgoingWebhooksWrite,
          label: <Text type="primary">{webhook.is_webhook_enabled ? 'Disable' : 'Enable'}</Text>,
        },
        {
          label: (
            <CopyToClipboard key="uid" text={webhook.id} onCopy={() => openNotification('Webhook ID has been copied')}>
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
          onClick: () => {},
          // this.setState({
          //   confirmationModal: {
          //     isOpen: true,
          //     confirmText: 'Confirm',
          //     dismissText: 'Cancel',
          //     onConfirm: () => this.onDeleteClick(record.id),
          //     body: 'The action cannot be undone.',
          //     title: `Are you sure you want to delete webhook?`,
          //   } as Partial<ConfirmModalProps> as ConfirmModalProps,
          // }),
          requiredPermission: UserActions.OutgoingWebhooksWrite,
          label: (
            <HorizontalGroup spacing="xs">
              <IconButton tooltip="Remove" tooltipPlacement="top" variant="destructive" name="trash-alt" />
              <Text type="danger">Delete Webhook</Text>
            </HorizontalGroup>
          ),
        },
      ]}
    />
  );
};
