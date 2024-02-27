import React, { FC } from 'react';

import { HorizontalGroup, Tooltip, Icon, useStyles2, IconButton, Switch, Checkbox } from '@grafana/ui';

import { GTable } from 'components/GTable/GTable';
import IntegrationLogoWithTitle from 'components/IntegrationLogo/IntegrationLogoWithTitle';
import { Text } from 'components/Text/Text';

import { getStyles } from './OutgoingTab.styles';
import { ApiSchemas } from 'network/oncall-api/api.types';

interface ConnectedIntegrationsTableProps {
  allowDelete?: boolean;
  selectable?: boolean;
  onChange?: (integration: ApiSchemas['AlertReceiveChannel'], checked: boolean) => void;
  data: Array<ApiSchemas['AlertReceiveChannel']>;
}

const ConnectedIntegrationsTable: FC<ConnectedIntegrationsTableProps> = (props) => {
  return <GTable emptyText={'No integrations found'} rowKey="id" columns={getColumns(props)} data={props.data} />;
};

const getColumns = ({ allowDelete, selectable, onChange }: ConnectedIntegrationsTableProps) => [
  ...(selectable
    ? [
        {
          width: '5%',
          render: (integration: ApiSchemas['AlertReceiveChannel']) => (
            <Checkbox onChange={(event) => onChange(integration, event.currentTarget.checked)} />
          ),
        },
      ]
    : []),
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
