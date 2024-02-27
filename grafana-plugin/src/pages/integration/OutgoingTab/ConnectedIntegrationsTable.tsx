import React, { FC } from 'react';

import { HorizontalGroup, Tooltip, Icon, useStyles2, IconButton, Switch } from '@grafana/ui';

import { GTable } from 'components/GTable/GTable';
import { IntegrationLogoWithTitle } from 'components/IntegrationLogo/IntegrationLogoWithTitle';
import { Text } from 'components/Text/Text';

import { getStyles } from './OutgoingTab.styles';

interface ConnectedIntegrationsTableProps {
  allowDelete?: boolean;
}

const ConnectedIntegrationsTable: FC<ConnectedIntegrationsTableProps> = (props) => {
  const FAKE_INTEGRATIONS = [{ a: 'a' }];

  return (
    <GTable
      emptyText={FAKE_INTEGRATIONS ? 'No integrations found' : 'Loading...'}
      rowKey="id"
      columns={getColumns(props)}
      data={FAKE_INTEGRATIONS}
    />
  );
};

const getColumns = ({ allowDelete }: ConnectedIntegrationsTableProps) => [
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
    render: () => <ActionsColumn allowDelete={allowDelete} />,
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

const ActionsColumn = ({ allowDelete }: { allowDelete?: boolean }) => (
  <HorizontalGroup>
    <IconButton aria-label="Open integration in new tab" name="external-link-alt" />
    {allowDelete && <IconButton aria-label="Remove backsync" name="trash-alt" />}
  </HorizontalGroup>
);

export default ConnectedIntegrationsTable;
