import React, { useState } from 'react';

import { Button, HorizontalGroup, Icon, Input, Modal, useStyles2 } from '@grafana/ui';

import { Text } from 'components/Text/Text';

import ConnectedIntegrationsTable from './ConnectedIntegrationsTable';
import { getStyles } from './OutgoingTab.styles';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useCommonStyles } from 'utils/hooks';

export const ConnectIntegrationModal = ({ onDismiss }: { onDismiss: () => void }) => {
  const commonStyles = useCommonStyles();
  const [selectedIntegrations, setSelectedIntegrations] = useState<Array<ApiSchemas['AlertReceiveChannel']>>([]);
  const styles = useStyles2(getStyles);

  const onChange = (integration: ApiSchemas['AlertReceiveChannel'], checked) => {
    if (checked) {
      setSelectedIntegrations([...selectedIntegrations, integration]);
    } else {
      setSelectedIntegrations(selectedIntegrations.filter(({ id }) => id !== integration.id));
    }
  };

  return (
    <Modal
      isOpen
      title={<Text.Title level={4}>Connect integration</Text.Title>}
      closeOnBackdropClick={false}
      closeOnEscape
      onDismiss={onDismiss}
    >
      <Input
        className={styles.searchIntegrationsInput}
        suffix={<Icon name="search" />}
        placeholder="Search integrations..."
      />
      <ConnectedIntegrationsTable data={[{ a: 'a' } as any]} selectable onChange={onChange} />
      <div className={commonStyles.bottomDrawerButtons}>
        <HorizontalGroup justify="flex-end">
          <Button variant="secondary" onClick={onDismiss}>
            Connect
          </Button>
          <Button variant="secondary" onClick={onDismiss}>
            Close
          </Button>
        </HorizontalGroup>
      </div>
    </Modal>
  );
};
