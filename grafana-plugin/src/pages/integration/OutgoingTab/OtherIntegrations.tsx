import React, { useState } from 'react';

import { Button, HorizontalGroup } from '@grafana/ui';
import { observer } from 'mobx-react-lite';

import { IntegrationBlock } from 'components/Integrations/IntegrationBlock';
import { IntegrationTag } from 'components/Integrations/IntegrationTag';

import { ConnectIntegrationModal } from './ConnectIntegrationModal';
import ConnectedIntegrationsTable from './ConnectedIntegrationsTable';

export const OtherIntegrations = observer(() => {
  const [isConnectModalOpened, setIsConnectModalOpened] = useState(false);

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
        content={<ConnectedIntegrationsTable allowDelete data={[]} />}
      />
    </>
  );
});
