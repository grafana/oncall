import React from 'react';

import { Icon, Input, Modal, useStyles2 } from '@grafana/ui';

import { Text } from 'components/Text/Text';

import ConnectedIntegrationsTable from './ConnectedIntegrationsTable';
import { getStyles } from './OutgoingTab.styles';

export const ConnectIntegrationModal = ({ onDismiss }: { onDismiss: () => void }) => {
  const styles = useStyles2(getStyles);

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
      <ConnectedIntegrationsTable />
    </Modal>
  );
};
