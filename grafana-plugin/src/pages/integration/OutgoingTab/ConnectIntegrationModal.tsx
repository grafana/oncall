import React, { useEffect, useState } from 'react';

import { Button, HorizontalGroup, Icon, Input, Modal, useStyles2 } from '@grafana/ui';
import cn from 'classnames';
import { debounce } from 'lodash-es';
import { observer } from 'mobx-react';

import { Text } from 'components/Text/Text';
import { AlertReceiveChannelHelper } from 'models/alert_receive_channel/alert_receive_channel.helpers';
import { ActionKey } from 'models/loader/action-keys';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useStore } from 'state/useStore';
import { useCommonStyles, useIsLoading } from 'utils/hooks';

import ConnectedIntegrationsTable from './ConnectedIntegrationsTable';
import { useCurrentIntegration } from './OutgoingTab.hooks';
import { getStyles } from './OutgoingTab.styles';

const DEBOUNCE_MS = 500;

export const ConnectIntegrationModal = observer(({ onDismiss }: { onDismiss: () => void }) => {
  const { alertReceiveChannelStore, alertReceiveChannelConnectedChannelsStore } = useStore();
  const currentIntegration = useCurrentIntegration();
  const isLoading = useIsLoading(ActionKey.FETCH_INTEGRATIONS_AVAILABLE_FOR_CONNECTION);
  const commonStyles = useCommonStyles();
  const [selectedIntegrations, setSelectedIntegrations] = useState<Array<ApiSchemas['AlertReceiveChannel']>>([]);
  const [page, setPage] = useState(1);
  const styles = useStyles2(getStyles);

  const { count, results, page_size } = AlertReceiveChannelHelper.getPaginatedSearchResult(alertReceiveChannelStore);

  useEffect(() => {
    fetchItems();
    return alertReceiveChannelStore.resetPaginatedResults;
  }, [page]);

  const fetchItems = async (search?: string) => {
    await alertReceiveChannelConnectedChannelsStore.fetchItemsAvailableForConnection({
      page,
      search,
      currentIntegrationId: currentIntegration.id,
    });
  };

  const onChange = (integration: ApiSchemas['AlertReceiveChannel'], checked) => {
    if (checked) {
      setSelectedIntegrations((integrations) => [...integrations, integration]);
    } else {
      setSelectedIntegrations((integrations) => integrations.filter(({ id }) => id !== integration.id));
    }
  };

  const onConnect = async (integrationsToConnect: typeof selectedIntegrations) => {
    await alertReceiveChannelConnectedChannelsStore.connectChannels(
      currentIntegration.id,
      integrationsToConnect.map(({ id }) => ({ id, backsync: false }))
    );
    onDismiss();
  };

  const debouncedSearch = debounce(fetchItems, DEBOUNCE_MS);

  const onSearchInputChange = (searchTerm: string) => {
    debouncedSearch(searchTerm);
  };

  const onChangePage = (page: number) => {
    setPage(page);
  };

  return (
    <Modal
      isOpen
      title={<Text.Title level={4}>Connect integration</Text.Title>}
      closeOnBackdropClick={false}
      closeOnEscape
      onDismiss={onDismiss}
      contentClassName={styles.connectIntegrationModalContent}
    >
      <Input
        className={styles.searchIntegrationsInput}
        suffix={<Icon name="search" />}
        placeholder="Search integrations..."
        onChange={(e) => onSearchInputChange(e.currentTarget.value)}
      />
      <ConnectedIntegrationsTable
        selectable
        onChange={onChange}
        tableProps={{
          data: results,
          pagination: {
            page,
            total: results ? Math.ceil((count || 0) / page_size) : 0,
            onChange: onChangePage,
          },
          emptyText: isLoading ? 'Loading...' : 'No integrations found',
        }}
      />
      <div
        className={cn(commonStyles.bottomDrawerButtons, {
          [styles.connectIntegrationModalButtons]: count > page_size,
        })}
      >
        <HorizontalGroup justify="flex-end">
          <Button variant="secondary" onClick={onDismiss}>
            Close
          </Button>
          <Button
            variant="primary"
            onClick={() => onConnect(selectedIntegrations)}
            disabled={!selectedIntegrations?.length}
          >
            Connect
          </Button>
        </HorizontalGroup>
      </div>
    </Modal>
  );
});
