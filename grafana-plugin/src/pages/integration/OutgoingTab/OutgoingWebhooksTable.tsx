import React, { FC, ReactElement, useEffect } from 'react';

import { IconButton, HorizontalGroup, Icon, ConfirmModal, useStyles2 } from '@grafana/ui';
import { observer } from 'mobx-react';
import CopyToClipboard from 'react-copy-to-clipboard';

import { GTable } from 'components/GTable/GTable';
import { HamburgerContextMenu } from 'components/HamburgerContextMenu/HamburgerContextMenu';
import { Text } from 'components/Text/Text';
import { WebhookLastEventTimestamp } from 'components/Webhooks/WebhookLastEventTimestamp';
import { WebhookName } from 'components/Webhooks/WebhookName';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useStore } from 'state/useStore';
import { LocationHelper } from 'utils/LocationHelper';
import { UserActions } from 'utils/authorization/authorization';
import { useConfirmModal } from 'utils/hooks';
import { openNotification } from 'utils/utils';

import { useIntegrationIdFromUrl } from './OutgoingTab.hooks';
import { getStyles } from './OutgoingTab.styles';
import { OutgoingTabDrawerKey, TriggerDetailsQueryStringKey, TriggerDetailsTab } from './OutgoingTab.types';

interface OutgoingWebhooksTableProps {
  openDrawer: (key: OutgoingTabDrawerKey) => void;
  noItemsInfo?: ReactElement;
}

export const OutgoingWebhooksTable: FC<OutgoingWebhooksTableProps> = observer(({ openDrawer, noItemsInfo }) => {
  const styles = useStyles2(getStyles);
  const {
    alertReceiveChannelWebhooksStore: { items, fetchItems },
  } = useStore();
  const integrationId = useIntegrationIdFromUrl();
  const itemsAsList = Object.values(items);

  useEffect(() => {
    fetchItems(integrationId);
  }, []);

  const openTriggerDetailsDrawer = (tab: TriggerDetailsTab, webhookId: string) => {
    LocationHelper.update(
      { [TriggerDetailsQueryStringKey.ActiveTab]: tab, [TriggerDetailsQueryStringKey.WebhookId]: webhookId },
      'partial'
    );
    openDrawer('webhookDetails');
  };

  if (!itemsAsList?.length && noItemsInfo) {
    return noItemsInfo;
  }
  return (
    <GTable
      emptyText={items ? 'No outgoing webhooks found' : 'Loading...'}
      rowKey="id"
      columns={getColumns(openTriggerDetailsDrawer)}
      data={itemsAsList}
      className={styles.outgoingWebhooksTable}
    />
  );
});

const getColumns = (openTriggerDetailsDrawer: (tab: TriggerDetailsTab, webhookId: string) => void) => [
  {
    width: '35%',
    title: <Text type="secondary">Trigger type</Text>,
    dataIndex: 'trigger_type_name',
    render: (name: string, webhook: ApiSchemas['Webhook']) => (
      <WebhookName name={name} isEnabled={webhook.is_webhook_enabled} />
    ),
  },
  {
    width: '65%',
    title: <Text type="secondary">Last event</Text>,
    render: (webhook: ApiSchemas['Webhook']) => (
      <WebhookLastEventTimestamp
        webhook={webhook}
        openDrawer={() => openTriggerDetailsDrawer(TriggerDetailsTab.LastEvent, webhook.id)}
      />
    ),
  },
  {
    key: 'action',
    render: (webhook: ApiSchemas['Webhook']) => (
      <OutgoingWebhookContextMenu webhook={webhook} openDrawer={openTriggerDetailsDrawer} />
    ),
  },
];

const OutgoingWebhookContextMenu = observer(
  ({
    webhook,
    openDrawer,
  }: {
    webhook: ApiSchemas['Webhook'];
    openDrawer: (tab: TriggerDetailsTab, webhookId: string) => void;
  }) => {
    const { alertReceiveChannelWebhooksStore } = useStore();
    const { modalProps, openModal } = useConfirmModal();
    const integrationId = useIntegrationIdFromUrl();

    return (
      <>
        <ConfirmModal {...modalProps} />
        <HamburgerContextMenu
          items={[
            {
              onClick: () => {
                openDrawer(TriggerDetailsTab.Settings, webhook.id);
              },
              requiredPermission: UserActions.OutgoingWebhooksWrite,
              label: <Text type="primary">Webhook settings</Text>,
            },
            {
              onClick: () => {
                openDrawer(TriggerDetailsTab.LastEvent, webhook.id);
              },
              requiredPermission: UserActions.OutgoingWebhooksRead,
              label: <Text type="primary">View Last Event</Text>,
            },
            {
              onClick: () => {
                openModal({
                  onConfirm: async () => {
                    await alertReceiveChannelWebhooksStore[webhook.is_webhook_enabled ? 'disable' : 'enable'](
                      integrationId,
                      webhook.id
                    );
                  },
                  title: `Are you sure you want to ${
                    webhook.is_webhook_enabled ? 'disable' : 'enable'
                  } outgoing webhook?`,
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
                  confirmText: 'Delete',
                  onConfirm: async () => {
                    await alertReceiveChannelWebhooksStore.delete(integrationId, webhook.id);
                  },
                  title: `Are you sure you want to delete outgoing webhook?`,
                });
              },
              requiredPermission: UserActions.OutgoingWebhooksWrite,
              label: (
                <HorizontalGroup spacing="xs">
                  <IconButton tooltip="Remove" tooltipPlacement="top" variant="destructive" name="trash-alt" />
                  <Text type="danger">Delete webhook</Text>
                </HorizontalGroup>
              ),
            },
          ]}
        />
      </>
    );
  }
);
