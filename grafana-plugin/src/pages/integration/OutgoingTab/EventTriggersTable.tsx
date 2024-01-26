import React, { useEffect } from 'react';

import { IconButton, HorizontalGroup, Icon } from '@grafana/ui';
import { observer } from 'mobx-react-lite';
import CopyToClipboard from 'react-copy-to-clipboard';

import GTable from 'components/GTable/GTable';
import HamburgerContextMenu from 'components/HamburgerContextMenu/HamburgerContextMenu';
import Text from 'components/Text/Text';
import { WebhookLastEvent } from 'components/Webhooks/WebhookLastEvent';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
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
    width: '60%',
    title: 'Last event',
    render: (webhook: OutgoingWebhook) => <WebhookLastEvent webhook={webhook} openDrawer={openDrawer} />,
  },
  {
    width: '5%',
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
        <div
          key="view-last-run"
          onClick={() => {
            onOpenDrawer(TriggerDetailsTab.LastEvent);
          }}
        >
          <WithPermissionControlTooltip key={'status_action'} userAction={UserActions.OutgoingWebhooksRead}>
            <Text type="primary">View Last Run</Text>
          </WithPermissionControlTooltip>
        </div>,
        <div
          key="settings"
          onClick={() => {
            onOpenDrawer(TriggerDetailsTab.Settings);
          }}
        >
          <WithPermissionControlTooltip key={'edit_action'} userAction={UserActions.OutgoingWebhooksWrite}>
            <Text type="primary">Edit settings</Text>
          </WithPermissionControlTooltip>
        </div>,
        <div
          key="enable-disable"
          onClick={
            () => {}
            // this.setState({
            //   confirmationModal: {
            //     isOpen: true,
            //     confirmText: 'Confirm',
            //     dismissText: 'Cancel',
            //     onConfirm: () => this.onDisableWebhook(record.id, !record.is_webhook_enabled),
            //     title: `Are you sure you want to ${record.is_webhook_enabled ? 'disable' : 'enable'} webhook?`,
            //   } as ConfirmModalProps,
            // })
          }
        >
          <WithPermissionControlTooltip key={'disable_action'} userAction={UserActions.OutgoingWebhooksWrite}>
            <Text type="primary">{webhook.is_webhook_enabled ? 'Disable' : 'Enable'}</Text>
          </WithPermissionControlTooltip>
        </div>,
        <CopyToClipboard key="uid" text={webhook.id} onCopy={() => openNotification('Webhook ID has been copied')}>
          <div>
            <HorizontalGroup type="primary" spacing="xs">
              <Icon name="clipboard-alt" />
              <Text type="primary">UID: {webhook.id}</Text>
            </HorizontalGroup>
          </div>
        </CopyToClipboard>,
        'divider',
        <div
          key="delete"
          onClick={
            () => {}
            // this.setState({
            //   confirmationModal: {
            //     isOpen: true,
            //     confirmText: 'Confirm',
            //     dismissText: 'Cancel',
            //     onConfirm: () => this.onDeleteClick(record.id),
            //     body: 'The action cannot be undone.',
            //     title: `Are you sure you want to delete webhook?`,
            //   } as Partial<ConfirmModalProps> as ConfirmModalProps,
            // })
          }
        >
          <WithPermissionControlTooltip key={'delete_action'} userAction={UserActions.OutgoingWebhooksWrite}>
            <HorizontalGroup spacing="xs">
              <IconButton tooltip="Remove" tooltipPlacement="top" variant="destructive" name="trash-alt" />
              <Text type="danger">Delete Webhook</Text>
            </HorizontalGroup>
          </WithPermissionControlTooltip>
        </div>,
      ]}
    />
  );
};
