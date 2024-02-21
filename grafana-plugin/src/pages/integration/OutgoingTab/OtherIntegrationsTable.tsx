import React, { useEffect } from 'react';

import { Button, HorizontalGroup, Icon, IconButton, Switch, Tooltip, useStyles2 } from '@grafana/ui';
import { observer } from 'mobx-react-lite';

import { GTable } from 'components/GTable/GTable';
import IntegrationLogoWithTitle from 'components/IntegrationLogo/IntegrationLogoWithTitle';
import { IntegrationBlock } from 'components/Integrations/IntegrationBlock';
import IntegrationTag from 'components/Integrations/IntegrationTag';
import { Text } from 'components/Text/Text';
import { useStore } from 'state/useStore';

import { getStyles } from './OutgoingTab.styles';
import { OutgoingTabDrawerKey } from './OutgoingTab.types';


export const OtherIntegrationsTable = observer(
  ({ openDrawer }: { openDrawer: (key: OutgoingTabDrawerKey) => void }) => {
    const {
      outgoingWebhookStore: { getSearchResult, updateItems },
    } = useStore();

    useEffect(() => {
      updateItems();
    }, []);

    const webhooks = getSearchResult();

    return (
      <IntegrationBlock
        heading={
          <HorizontalGroup justify="space-between">
            <IntegrationTag>Send data from other integrations</IntegrationTag>
            <Button size="sm" variant="secondary">
              Connect
            </Button>
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
