import React, { useEffect, useState } from 'react';

import { HorizontalGroup } from '@grafana/ui';
import { observer } from 'mobx-react';

import { Button } from 'components/Button/Button';
import { IntegrationBlock } from 'components/Integrations/IntegrationBlock';
import { IntegrationTag } from 'components/Integrations/IntegrationTag';
import { Text } from 'components/Text/Text';
import { useStore } from 'state/useStore';

import { ConnectIntegrationModal } from './ConnectIntegrationModal';
import ConnectedIntegrationsTable from './ConnectedIntegrationsTable';
import { useIntegrationIdFromUrl } from './OutgoingTab.hooks';

export const OtherIntegrations = observer(() => {
  const {
    alertReceiveChannelConnectedChannelsStore: { fetchItems, itemsAsList, toggleBacksync },
  } = useStore();
  const sourceIntegrationId = useIntegrationIdFromUrl();
  const [isConnectModalOpened, setIsConnectModalOpened] = useState(false);

  useEffect(() => {
    fetchItems(sourceIntegrationId);
  }, [sourceIntegrationId]);

  return (
    <>
      {isConnectModalOpened && <ConnectIntegrationModal onDismiss={() => setIsConnectModalOpened(false)} />}
      <IntegrationBlock
        heading={
          <HorizontalGroup justify="space-between">
            <IntegrationTag>Send data from other integrations</IntegrationTag>
            <Button size="sm" variant="secondary" onClick={() => setIsConnectModalOpened(true)}>
              Connect
            </Button>
          </HorizontalGroup>
        }
        content={
          itemsAsList?.length ? (
            <ConnectedIntegrationsTable
              allowDelete
              allowBacksync
              tableProps={{
                data: itemsAsList.map(({ alert_receive_channel }) => alert_receive_channel),
              }}
              defaultBacksyncedIds={itemsAsList
                .filter(({ backsync }) => backsync)
                .map(({ alert_receive_channel: { id } }) => id)}
              onBacksyncChange={(connectedChannelId: string, backsync: boolean) =>
                toggleBacksync({
                  sourceIntegrationId,
                  connectedChannelId,
                  backsync,
                })
              }
            />
          ) : (
            <HorizontalGroup align="center">
              <Text type="secondary">There are no connected integrations.</Text>
              <Button variant="primary" showAsLink onClick={() => setIsConnectModalOpened(true)}>
                Connect them
              </Button>
            </HorizontalGroup>
          )
        }
      />
    </>
  );
});
