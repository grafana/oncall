import React, { useMemo, useState } from 'react';

import { css, cx } from '@emotion/css';
import { ConfirmModal, Icon, IconName, Stack, useStyles2 } from '@grafana/ui';
import { StackSize } from 'helpers/consts';
import { observer } from 'mobx-react';

import { IntegrationBlock } from 'components/Integrations/IntegrationBlock';
import { PluginLink } from 'components/PluginLink/PluginLink';
import { Text } from 'components/Text/Text';
import { RouteButtonsDisplay } from 'containers/IntegrationContainers/ExpandedIntegrationRouteDisplay/ExpandedIntegrationRouteDisplay';
import { RouteHeading } from 'containers/IntegrationContainers/RouteHeading';
import { ChannelFilter } from 'models/channel_filter/channel_filter.types';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { CommonIntegrationHelper } from 'pages/integration/CommonIntegration.helper';
import { IntegrationHelper } from 'pages/integration/Integration.helper';
import { getIntegrationStyles } from 'pages/integration/Integration.styles';
import { useStore } from 'state/useStore';

interface CollapsedIntegrationRouteDisplayProps {
  alertReceiveChannelId: ApiSchemas['AlertReceiveChannel']['id'];
  channelFilterId: ChannelFilter['id'];
  routeIndex: number;
  toggle: () => void;
  openEditTemplateModal: (templateName: string | string[], channelFilterId?: ChannelFilter['id']) => void;
  onEditRegexpTemplate: (channelFilterId: ChannelFilter['id']) => void;
  onRouteDelete: (routeId: string) => void;
  onItemMove: () => void;
}

export const CollapsedIntegrationRouteDisplay: React.FC<CollapsedIntegrationRouteDisplayProps> = observer(
  ({
    channelFilterId,
    alertReceiveChannelId,
    routeIndex,
    toggle,
    openEditTemplateModal,
    onEditRegexpTemplate,
    onRouteDelete,
    onItemMove,
  }) => {
    const store = useStore();
    const styles = useStyles2(getStyles);
    const integrationStyles = useStyles2(getIntegrationStyles);

    const { escalationChainStore, alertReceiveChannelStore } = store;
    const [routeIdForDeletion, setRouteIdForDeletion] = useState<ChannelFilter['id']>(undefined);

    const channelFilter = alertReceiveChannelStore.channelFilters[channelFilterId];

    const routeWording = useMemo(() => {
      return CommonIntegrationHelper.getRouteConditionWording(
        alertReceiveChannelStore.channelFilterIds[alertReceiveChannelId],
        routeIndex
      );
    }, [routeIndex, alertReceiveChannelStore.channelFilterIds[alertReceiveChannelId]]);

    if (!channelFilter) {
      return null;
    }

    const escalationChain = escalationChainStore.items[channelFilter.escalation_chain];
    const chatOpsAvailableChannels = IntegrationHelper.getChatOpsChannels(channelFilter, store).filter(
      (channel) => channel
    );

    return (
      <>
        <IntegrationBlock
          noContent={false}
          key={channelFilterId}
          toggle={toggle}
          heading={
            <div className={styles.headingContainer}>
              <RouteHeading
                className={cx(styles.headingContainerItem, styles.headingContainerItemLarge)}
                routeWording={routeWording}
                routeIndex={routeIndex}
                channelFilter={channelFilter}
                channelFilterIds={alertReceiveChannelStore.channelFilterIds[alertReceiveChannelId]}
              />

              <div className={styles.headingContainerItem}>
                <RouteButtonsDisplay
                  alertReceiveChannelId={alertReceiveChannelId}
                  channelFilterId={channelFilterId}
                  routeIndex={routeIndex}
                  onItemMove={onItemMove}
                  setRouteIdForDeletion={() => setRouteIdForDeletion(channelFilterId)}
                  openRouteTemplateEditor={() => handleEditRoutingTemplate(channelFilter, channelFilterId)}
                />
              </div>
            </div>
          }
          content={
            <div>
              <div className={styles.collapsedRouteContainer}>
                {chatOpsAvailableChannels.length > 0 && (
                  <div className={styles.collapsedRouteItem}>
                    <Stack gap={StackSize.xs}>
                      <Text type="secondary">Publish to ChatOps</Text>

                      {chatOpsAvailableChannels.map(
                        (chatOpsChannel: { name: string; icon: IconName }, chatOpsIndex) => (
                          <div
                            key={`${chatOpsChannel.name}-${chatOpsIndex}`}
                            className={
                              chatOpsIndex === chatOpsAvailableChannels.length
                                ? ''
                                : css`
                                    margin-right: 4px;
                                  `
                            }
                          >
                            <Icon name={chatOpsChannel.icon} className={styles.icon} />
                            <Text type="primary">{chatOpsChannel.name}</Text>
                          </div>
                        )
                      )}
                    </Stack>
                  </div>
                )}

                <div className={styles.collapsedRouteItem}>
                  <div
                    className={css`
                      display: flex;
                      align-items: center;
                      gap: 4px;
                    `}
                  >
                    <Icon name="list-ui-alt" />
                    <Text
                      type="secondary"
                      className={css`
                        margin-right: 4px;
                      `}
                    >
                      Trigger escalation chain
                    </Text>
                  </div>

                  {escalationChain?.name && (
                    <PluginLink target="_blank" query={{ page: 'escalations', id: channelFilter.escalation_chain }}>
                      <Text type="primary">{escalationChain?.name}</Text>
                    </PluginLink>
                  )}

                  {!escalationChain?.name && (
                    <div
                      className={css`
                        display: flex;
                        align-items: center;
                        gap: 4px;
                      `}
                    >
                      <div className={integrationStyles.iconExclamation}>
                        <Icon name="exclamation-triangle" />
                      </div>
                      <Text type="primary" data-testid="integration-escalation-chain-not-selected">
                        Not selected
                      </Text>
                    </div>
                  )}
                </div>
              </div>
            </div>
          }
        />
        {routeIdForDeletion && (
          <ConfirmModal
            isOpen
            title="Delete route?"
            body="Are you sure you want to delete this route?"
            confirmText="Delete"
            icon="exclamation-triangle"
            onConfirm={onRouteDeleteConfirm}
            onDismiss={() => setRouteIdForDeletion(undefined)}
          />
        )}
      </>
    );

    function handleEditRoutingTemplate(channelFilter, channelFilterId) {
      if (channelFilter.filtering_term_type === 0) {
        onEditRegexpTemplate(channelFilterId);
      } else {
        openEditTemplateModal('route_template', channelFilterId);
      }
    }

    async function onRouteDeleteConfirm() {
      setRouteIdForDeletion(undefined);
      onRouteDelete(routeIdForDeletion);
    }
  }
);

const getStyles = () => {
  return {
    headingContainer: css`
      width: 100%;
      display: flex;
      flex-direction: row;
      flex-wrap: nowrap;
      overflow: hidden;
      gap: 12px;
    `,

    headingContainerItem: css`
      display: flex;
      white-space: nowrap;
      flex-direction: row;
      gap: 8px;
    `,

    headingContainerItemLarge: css`
      flex-grow: 1;
      overflow: hidden;
    `,

    headingContainerText: css`
      overflow: hidden;
      max-width: calc(100% - 48px);
      text-overflow: ellipsis;
    `,

    icon: css`
      margin-right: 4px;
    `,

    collapsedRouteContainer: css`
      display: flex;
      flex-direction: row;
      flex-wrap: wrap;
      gap: 8px;
    `,

    collapsedRouteItem: css`
      display: flex;
      flex-direction: row;
    `,
  };
};
