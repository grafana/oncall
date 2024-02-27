import React, { FC, useMemo } from 'react';

import { HorizontalGroup, Tooltip, Icon, useStyles2, IconButton, Switch, Checkbox } from '@grafana/ui';

import { GTable, GTableProps } from 'components/GTable/GTable';
import { IntegrationLogoWithTitle } from 'components/IntegrationLogo/IntegrationLogoWithTitle';
import { Text } from 'components/Text/Text';

import { getStyles } from './OutgoingTab.styles';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { AlertReceiveChannelHelper } from 'models/alert_receive_channel/alert_receive_channel.helpers';
import { observer } from 'mobx-react';
import { useStore } from 'state/useStore';

interface ConnectedIntegrationsTableProps {
  allowDelete?: boolean;
  selectable?: boolean;
  onChange?: (integration: ApiSchemas['AlertReceiveChannel'], checked: boolean) => void;
  tableProps: GTableProps;
}

const ConnectedIntegrationsTable: FC<ConnectedIntegrationsTableProps> = observer(
  ({ selectable, allowDelete, onChange, tableProps }) => {
    const { alertReceiveChannelStore } = useStore();

    const columns = useMemo(
      () => [
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
          dataIndex: 'verbal_name',
          render: (name: string) => name,
        },
        {
          width: '55%',
          title: <Text type="secondary">Type</Text>,
          render: (integration: ApiSchemas['AlertReceiveChannel']) => (
            <IntegrationLogoWithTitle
              integration={AlertReceiveChannelHelper.getIntegrationSelectOption(alertReceiveChannelStore, integration)}
            />
          ),
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
      ],
      []
    );

    return <GTable rowKey="id" columns={columns} {...tableProps} />;
  }
);

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
