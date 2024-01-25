import React, { useEffect } from 'react';

import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { useStyles2, Input, IconButton, Button, HorizontalGroup, Icon } from '@grafana/ui';
import { observer } from 'mobx-react-lite';
import CopyToClipboard from 'react-copy-to-clipboard';

import CopyToClipboardIcon from 'components/CopyToClipboardIcon/CopyToClipboardIcon';
import GTable from 'components/GTable/GTable';
import HamburgerContextMenu from 'components/HamburgerContextMenu/HamburgerContextMenu';
import IntegrationCollapsibleTreeView from 'components/IntegrationCollapsibleTreeView/IntegrationCollapsibleTreeView';
import IntegrationBlock from 'components/Integrations/IntegrationBlock';
import IntegrationTag from 'components/Integrations/IntegrationTag';
import Text from 'components/Text/Text';
import { WebhookLastEvent } from 'components/Webhooks/WebhookLastEvent';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { OutgoingWebhook } from 'models/outgoing_webhook/outgoing_webhook.types';
import { useStore } from 'state/useStore';
import { openNotification } from 'utils';
import { UserActions } from 'utils/authorization';

const OutgoingTab = () => {
  return (
    <>
      <IntegrationCollapsibleTreeView
        configElements={[
          { customIcon: 'plug', expandedView: () => <Url /> },
          {
            customIcon: 'plus',
            expandedView: () => <AddEventTrigger />,
          },
        ]}
      />
      <EventTriggersTable />
    </>
  );
};

const Url = () => {
  const styles = useStyles2(getStyles);
  const FAKE_URL = 'https://example.com';

  const value = FAKE_URL;

  return (
    <div>
      <IntegrationBlock
        noContent
        className={styles.urlIntegrationBlock}
        heading={
          <div className={styles.horizontalGroup}>
            <IntegrationTag>ServiceNow URL</IntegrationTag>
            <Input
              value={value}
              disabled
              className={styles.urlInput}
              suffix={
                <>
                  <CopyToClipboardIcon text={FAKE_URL} />
                  <IconButton
                    aria-label="Open in new tab"
                    name="external-link-alt"
                    onClick={() => window.open(value, '_blank')}
                  />
                </>
              }
            />
            <HamburgerContextMenu
              items={[<div key="url">URL Settings</div>]}
              hamburgerIconClassName={styles.hamburgerIcon}
            />
          </div>
        }
      />
      <h4>Outgoing events</h4>
      <div>
        <Text type="secondary">Webhooks managed by this integration.</Text>
      </div>
    </div>
  );
};

const AddEventTrigger = () => {
  const styles = useStyles2(getStyles);

  return (
    <Button onClick={() => {}} className={styles.addEventTriggerBtn}>
      Add Event Trigger
    </Button>
  );
};

const columns = [
  {
    width: '25%',
    title: 'Event Trigger',
    dataIndex: 'trigger_type_name',
    render: (triggerType: string) => <>{triggerType}</>,
  },
  {
    width: '10%',
    title: 'Last event',
    render: (webhook: OutgoingWebhook) => <WebhookLastEvent webhook={webhook} openLastEvent={() => {}} />,
  },
  {
    width: '20%',
    key: 'action',
    render: (webhook: OutgoingWebhook) => <EventTriggerContextMenu webhook={webhook} />,
  },
];

const EventTriggerContextMenu = ({ webhook }: { webhook: OutgoingWebhook }) => {
  const {
    drawerStore: { openDrawer },
  } = useStore();

  return (
    <HamburgerContextMenu
      items={[
        <div key="view-last-run" onClick={() => openDrawer({ drawerKey: 'OutgoingEventTrigger', data: webhook })}>
          <WithPermissionControlTooltip key={'status_action'} userAction={UserActions.OutgoingWebhooksRead}>
            <Text type="primary">View Last Run</Text>
          </WithPermissionControlTooltip>
        </div>,
        <div key="settings" onClick={() => {}}>
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

const EventTriggersTable = observer(() => {
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
      columns={columns}
      data={webhooks}
    />
  );
});

export const getStyles = (theme: GrafanaTheme2) => ({
  urlIntegrationBlock: css({
    marginBottom: '32px',
  }),
  urlInput: css({
    height: '25px',
    background: theme.colors.background.canvas,
    '& input': {
      height: '25px',
    },
  }),
  hamburgerIcon: css({
    background: theme.colors.secondary.shade,
  }),
  horizontalGroup: css({
    display: 'flex',
    gap: '8px',
  }),
  addEventTriggerBtn: css({
    marginTop: '16px',
  }),
});

export default OutgoingTab;
