import React, { useEffect, useState } from 'react';

import { Button, HorizontalGroup, Icon, Input, Modal, useStyles2 } from '@grafana/ui';
import cn from 'classnames';

import { Text } from 'components/Text/Text';

import ConnectedIntegrationsTable from './ConnectedIntegrationsTable';
import { getStyles } from './OutgoingTab.styles';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useCommonStyles, useIsLoading } from 'utils/hooks';
import { observer } from 'mobx-react-lite';
import { useStore } from 'state/useStore';
import { AlertReceiveChannelHelper } from 'models/alert_receive_channel/alert_receive_channel.helpers';
import { ActionKey } from 'models/loader/action-keys';
import { debounce } from 'lodash-es';

const DEBOUNCE_MS = 500;

export const ConnectIntegrationModal = observer(({ onDismiss }: { onDismiss: () => void }) => {
  const { alertReceiveChannelStore } = useStore();
  const isLoading = useIsLoading(ActionKey.FETCH_INTEGRATIONS);
  const commonStyles = useCommonStyles();
  const [selectedIntegrations, setSelectedIntegrations] = useState<Array<ApiSchemas['AlertReceiveChannel']>>([]);
  const [page, setPage] = useState(1);
  const styles = useStyles2(getStyles);

  const { count, results, page_size } = AlertReceiveChannelHelper.getPaginatedSearchResult(alertReceiveChannelStore);

  useEffect(() => {
    fetchItems();
  }, [page]);

  const fetchItems = async (search?: string) => {
    // TODO: openapi schema should be updated to support servicenow
    await alertReceiveChannelStore.fetchPaginatedItems({
      filters: { integration_ne: ['servicenow' as any], search },
      perpage: 10,
      page,
    });
  };

  const onChange = (integration: ApiSchemas['AlertReceiveChannel'], checked) => {
    if (checked) {
      setSelectedIntegrations([...selectedIntegrations, integration]);
    } else {
      setSelectedIntegrations(selectedIntegrations.filter(({ id }) => id !== integration.id));
    }
  };

  const onConnect = () => {
    console.log(selectedIntegrations);
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
      <div className={cn(commonStyles.bottomDrawerButtons, styles.connectIntegrationModalButtons)}>
        <HorizontalGroup justify="flex-end">
          <Button variant="primary" onClick={onConnect}>
            Connect
          </Button>
          <Button variant="secondary" onClick={onDismiss}>
            Close
          </Button>
        </HorizontalGroup>
      </div>
    </Modal>
  );
});
