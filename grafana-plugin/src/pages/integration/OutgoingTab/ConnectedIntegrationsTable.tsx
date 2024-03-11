import React, { FC } from 'react';

import { HorizontalGroup, Tooltip, Icon, useStyles2, IconButton, Switch, Checkbox, ConfirmModal } from '@grafana/ui';
import { observer } from 'mobx-react';
import Emoji from 'react-emoji-render';

import { GTable, GTableProps } from 'components/GTable/GTable';
import { IntegrationLogoWithTitle } from 'components/IntegrationLogo/IntegrationLogoWithTitle';
import { Text } from 'components/Text/Text';
import { AlertReceiveChannelHelper } from 'models/alert_receive_channel/alert_receive_channel.helpers';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useStore } from 'state/useStore';
import { PLUGIN_ROOT } from 'utils/consts';
import { useConfirmModal } from 'utils/hooks';

import { useIntegrationIdFromUrl } from './OutgoingTab.hooks';
import { getStyles } from './OutgoingTab.styles';

type ConnectedIntegration =
  | ApiSchemas['AlertReceiveChannelConnectedChannel']['alert_receive_channel']
  | ApiSchemas['AlertReceiveChannel'];

interface ConnectedIntegrationsTableProps {
  allowDelete?: boolean;
  allowBacksync?: boolean;
  onBacksyncChange?: (id: string, checked: boolean) => void;
  defaultBacksyncedIds?: string[];
  selectable?: boolean;
  onChange?: (connecteIntegration: ConnectedIntegration, checked: boolean) => void;
  tableProps: GTableProps<ConnectedIntegration>;
}

const ConnectedIntegrationsTable: FC<ConnectedIntegrationsTableProps> = observer(
  ({ selectable, allowDelete, onChange, onBacksyncChange, tableProps, defaultBacksyncedIds = [], allowBacksync }) => {
    const { alertReceiveChannelStore } = useStore();

    const columns = [
      ...(selectable
        ? [
            {
              width: '5%',
              render: (connectedIntegration: ConnectedIntegration) => (
                <Checkbox onChange={(event) => onChange(connectedIntegration, event.currentTarget.checked)} />
              ),
            },
          ]
        : []),
      {
        width: '45%',
        title: <Text type="secondary">Integration name</Text>,
        render: ({ verbal_name }: ConnectedIntegration) => <Emoji text={verbal_name} />,
      },
      {
        width: '55%',
        title: <Text type="secondary">Type</Text>,
        render: (connectedIntegration: ConnectedIntegration) => {
          return (
            <IntegrationLogoWithTitle
              integration={AlertReceiveChannelHelper.getIntegrationSelectOption(
                alertReceiveChannelStore,
                connectedIntegration
              )}
            />
          );
        },
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
              render: (connectedIntegration: ConnectedIntegration) => (
                <BacksyncSwitcher
                  defaultChecked={defaultBacksyncedIds.includes(connectedIntegration.id)}
                  onChange={(checked: boolean) => onBacksyncChange(connectedIntegration.id, checked)}
                />
              ),
            },
          ]
        : []),
      {
        render: (connectedIntegration: ConnectedIntegration) => (
          <ActionsColumn allowDelete={allowDelete} connectedIntegration={connectedIntegration} />
        ),
      },
    ];

    return <GTable rowKey="id" columns={columns} {...tableProps} />;
  }
);

const BacksyncSwitcher = ({
  onChange,
  defaultChecked,
}: {
  onChange: (checked: boolean) => void;
  defaultChecked?: boolean;
}) => {
  const styles = useStyles2(getStyles);

  return (
    <div className={styles.backsyncColumn}>
      <Switch defaultChecked={defaultChecked} onChange={({ currentTarget }) => onChange(currentTarget.checked)} />
    </div>
  );
};

const ActionsColumn = ({
  allowDelete,
  connectedIntegration,
}: {
  allowDelete?: boolean;
  connectedIntegration: ConnectedIntegration;
}) => {
  const { alertReceiveChannelConnectedChannelsStore } = useStore();
  const sourceIntegrationId = useIntegrationIdFromUrl();
  const { modalProps, openModal } = useConfirmModal();

  return (
    <>
      <ConfirmModal {...modalProps} />
      <HorizontalGroup>
        <a href={`${PLUGIN_ROOT}/integrations/${connectedIntegration.id}`} target="_blank" rel="noreferrer">
          <IconButton aria-label="Open integration in new tab" name="external-link-alt" />
        </a>
        {allowDelete && (
          <IconButton
            aria-label="Remove backsync"
            name="trash-alt"
            onClick={() =>
              openModal({
                confirmText: 'Disconnect',
                onConfirm: async () => {
                  await alertReceiveChannelConnectedChannelsStore.deleteConnectedChannel({
                    sourceIntegrationId,
                    connectedIntegrationId: connectedIntegration.id,
                  });
                },
                title: `Are you sure you want to disconnect ${connectedIntegration.verbal_name} integration?`,
              })
            }
          />
        )}
      </HorizontalGroup>
    </>
  );
};

export default ConnectedIntegrationsTable;
