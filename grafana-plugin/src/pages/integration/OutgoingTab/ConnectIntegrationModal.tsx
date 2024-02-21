import React from 'react';

import { Modal } from '@grafana/ui';

import { Text } from 'components/Text/Text';

import ConnectedIntegrationsTable from './ConnectedIntegrationsTable';

export const ConnectIntegrationModal = ({ onDismiss }: { onDismiss: () => void }) => (
  <Modal
    isOpen
    title={<Text.Title level={4}>Connect integration</Text.Title>}
    closeOnBackdropClick={false}
    closeOnEscape
    onDismiss={onDismiss}
  >
    <ConnectedIntegrationsTable />
  </Modal>
);
