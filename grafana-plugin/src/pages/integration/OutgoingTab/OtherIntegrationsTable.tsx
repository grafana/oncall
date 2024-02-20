import React, { useEffect } from 'react';

import { observer } from 'mobx-react-lite';

import { GTable } from 'components/GTable/GTable';
import { Text } from 'components/Text/Text';
import { OutgoingWebhook } from 'models/outgoing_webhook/outgoing_webhook.types';
import { useStore } from 'state/useStore';
import { LocationHelper } from 'utils/LocationHelper';

import { OutgoingTabDrawerKey, TriggerDetailsQueryStringKey, TriggerDetailsTab } from './OutgoingTab.types';
import { IntegrationBlock } from 'components/Integrations/IntegrationBlock';
import IntegrationTag from 'components/Integrations/IntegrationTag';
import IntegrationLogoWithTitle from 'components/IntegrationLogo/IntegrationLogoWithTitle';
import { HorizontalGroup, Icon, IconButton, Switch, Tooltip, useStyles2 } from '@grafana/ui';
import { getStyles } from './OutgoingTab.styles';

export const OtherIntegrationsTable = observer(
  ({ openDrawer }: { openDrawer: (key: OutgoingTabDrawerKey) => void }) => {
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
      <IntegrationBlock
        heading={
          <HorizontalGroup justify="space-between">
            <IntegrationTag>Send data from other integrations</IntegrationTag>
            <IntegrationTag>Connect</IntegrationTag>
          </HorizontalGroup>
        }
        content={
          <GTable
            emptyText={webhooks ? 'No outgoing webhooks found' : 'Loading...'}
            rowKey="id"
            columns={getColumns()}
            data={webhooks}
          />
        }
      />
    );
  }
);

const getColumns = () => [
  {
    width: '45%',
    title: <Text type="secondary">Integration name</Text>,
    dataIndex: 'trigger_type_name',
    render: () => <>Some integration name</>,
  },
  {
    width: '55%',
    title: <Text type="secondary">Type</Text>,
    render: () => <IntegrationLogoWithTitle integration={{ value: 'elastalert', display_name: 'ElastAlerts' }} />,
  },
  {
    title: (
      <HorizontalGroup>
        <Text type="secondary">Backsync</Text>
        <Tooltip content={<>Switch on to start sending data from other integrations</>}>
          <Icon name={'info-circle'} />
        </Tooltip>
      </HorizontalGroup>
    ),
    render: BacksyncSwitcher,
  },
  {
    render: ActionsColumn,
  },
];

const BacksyncSwitcher = () => {
  const styles = useStyles2(getStyles);

  return (
    <div className={styles.backsyncColumn}>
      <Switch defaultChecked />
    </div>
  );
};

const ActionsColumn = () => (
  <HorizontalGroup>
    <IconButton aria-label="Open integration in new tab" name="external-link-alt" />
    <IconButton aria-label="Remove backsync" name="trash-alt" />
  </HorizontalGroup>
);
