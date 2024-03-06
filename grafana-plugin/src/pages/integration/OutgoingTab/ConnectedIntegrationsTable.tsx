import React, { FC } from 'react';

import { HorizontalGroup, Tooltip, Icon, useStyles2, IconButton, Switch, Checkbox } from '@grafana/ui';
import { observer } from 'mobx-react';

import { GTable, GTableProps } from 'components/GTable/GTable';
import { IntegrationLogoWithTitle } from 'components/IntegrationLogo/IntegrationLogoWithTitle';
import { Text } from 'components/Text/Text';
import { AlertReceiveChannelHelper } from 'models/alert_receive_channel/alert_receive_channel.helpers';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useStore } from 'state/useStore';

import { getStyles } from './OutgoingTab.styles';
import Emoji from 'react-emoji-render';

type Integration =
  | ApiSchemas['AlertReceiveChannelConnectedChannel']['alert_receive_channel']
  | ApiSchemas['AlertReceiveChannel'];

interface ConnectedIntegrationsTableProps {
  allowDelete?: boolean;
  allowBacksync?: boolean;
  onBacksyncChange?: (id: string, checked: boolean) => void;
  selectable?: boolean;
  onChange?: (integration: Integration, checked: boolean) => void;
  tableProps: GTableProps<Integration>;
}

const ConnectedIntegrationsTable: FC<ConnectedIntegrationsTableProps> = observer(
  ({ selectable, allowDelete, onChange, onBacksyncChange, tableProps, allowBacksync }) => {
    const { alertReceiveChannelStore } = useStore();

    const columns = [
      ...(selectable
        ? [
            {
              width: '5%',
              render: (integration: Integration) => (
                <Checkbox onChange={(event) => onChange(integration, event.currentTarget.checked)} />
              ),
            },
          ]
        : []),
      {
        width: '45%',
        title: <Text type="secondary">Integration name</Text>,
        render: ({ verbal_name }: Integration) => <Emoji text={verbal_name} />,
      },
      {
        width: '55%',
        title: <Text type="secondary">Type</Text>,
        render: (integration: Integration) => (
          <IntegrationLogoWithTitle
            integration={AlertReceiveChannelHelper.getIntegrationSelectOption(alertReceiveChannelStore, integration)}
          />
        ),
      },
      ...(allowBacksync
        ? [
            {
              title: (
                <HorizontalGroup>
                  <Text type="secondary">Backsync</Text>
                  <Tooltip content={<>Switch on to start sending data from other integrations</>}>
                    <Icon name={'info-circle'} />
                  </Tooltip>
                </HorizontalGroup>
              ),
              render: ({ alert_receive_channel }: ApiSchemas['AlertReceiveChannelConnectedChannel']) => (
                <BacksyncSwitcher
                  onChange={(checked: boolean) => onBacksyncChange(alert_receive_channel.id, checked)}
                />
              ),
            },
          ]
        : []),
      {
        render: () => <ActionsColumn allowDelete={allowDelete} />,
      },
    ];

    return <GTable rowKey="id" columns={columns} {...tableProps} />;
  }
);

const BacksyncSwitcher = ({ onChange }: { onChange: (checked: boolean) => void }) => {
  const styles = useStyles2(getStyles);

  return (
    <div className={styles.backsyncColumn}>
      <Switch onChange={({ currentTarget }) => onChange(currentTarget.checked)} />
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
