import React, { useState } from 'react';

import { ConfirmModal, HorizontalGroup, Icon, IconName } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import IntegrationBlock from 'components/Integrations/IntegrationBlock';
import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import TooltipBadge from 'components/TooltipBadge/TooltipBadge';
import styles from 'containers/IntegrationContainers/CollapsedIntegrationRouteDisplay/CollapsedIntegrationRouteDisplay.module.scss';
import { RouteButtonsDisplay } from 'containers/IntegrationContainers/ExpandedIntegrationRouteDisplay/ExpandedIntegrationRouteDisplay';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { ChannelFilter } from 'models/channel_filter';
import CommonIntegrationHelper from 'pages/integration/CommonIntegration.helper';
import IntegrationHelper from 'pages/integration/Integration.helper';
import { useStore } from 'state/useStore';
import { openNotification } from 'utils';

const cx = cn.bind(styles);

interface CollapsedIntegrationRouteDisplayProps {
  alertReceiveChannelId: AlertReceiveChannel['id'];
  channelFilterId: ChannelFilter['id'];
  routeIndex: number;
  toggle: () => void;
  openEditTemplateModal: (templateName: string | string[], channelFilterId?: ChannelFilter['id']) => void;
  onEditRegexpTemplate: (channelFilterId: ChannelFilter['id']) => void;
}

const CollapsedIntegrationRouteDisplay: React.FC<CollapsedIntegrationRouteDisplayProps> = observer(
  ({ channelFilterId, alertReceiveChannelId, routeIndex, toggle, openEditTemplateModal, onEditRegexpTemplate }) => {
    const store = useStore();
    const { escalationChainStore, alertReceiveChannelStore } = store;
    const [routeIdForDeletion, setRouteIdForDeletion] = useState<ChannelFilter['id']>(undefined);

    const channelFilter = alertReceiveChannelStore.channelFilters[channelFilterId];
    if (!channelFilter) {
      return null;
    }

    const escalationChain = escalationChainStore.items[channelFilter.escalation_chain];
    const routeWording = CommonIntegrationHelper.getRouteConditionWording(
      alertReceiveChannelStore.channelFilterIds[alertReceiveChannelId],
      routeIndex
    );
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
            <div className={cx('heading-container')}>
              <div className={cx('heading-container__item', 'heading-container__item--large')}>
                <TooltipBadge
                  borderType="success"
                  text={CommonIntegrationHelper.getRouteConditionWording(
                    alertReceiveChannelStore.channelFilterIds[alertReceiveChannelId],
                    routeIndex
                  )}
                  tooltipTitle={CommonIntegrationHelper.getRouteConditionTooltipWording(
                    alertReceiveChannelStore.channelFilterIds[alertReceiveChannelId],
                    routeIndex
                  )}
                  className={cx('u-margin-right-xs')}
                  tooltipContent={undefined}
                />
                {routeWording === 'Default' && <Text type="secondary">Unmatched alerts routed to default route</Text>}
                {routeWording !== 'Default' &&
                  (channelFilter.filtering_term ? (
                    <Text type="primary" className={cx('heading-container__text')}>
                      {channelFilter.filtering_term}
                    </Text>
                  ) : (
                    <>
                      <div className={cx('icon-exclamation')}>
                        <Icon name="exclamation-triangle" />
                      </div>
                      <Text type="primary" className={cx('heading-container__text')}>
                        Routing template not set
                      </Text>
                    </>
                  ))}
              </div>

              <div className={cx('heading-container__item')}>
                <RouteButtonsDisplay
                  alertReceiveChannelId={alertReceiveChannelId}
                  channelFilterId={channelFilterId}
                  routeIndex={routeIndex}
                  setRouteIdForDeletion={() => setRouteIdForDeletion(channelFilterId)}
                  openRouteTemplateEditor={() => handleEditRoutingTemplate(channelFilter, channelFilterId)}
                />
              </div>
            </div>
          }
          content={
            <div>
              <div className={cx('collapsedRoute__container')}>
                {chatOpsAvailableChannels.length > 0 && (
                  <div className={cx('collapsedRoute__item')}>
                    <HorizontalGroup spacing="xs">
                      <Text type="secondary">Publish to ChatOps</Text>

                      {chatOpsAvailableChannels.map(
                        (chatOpsChannel: { name: string; icon: IconName }, chatOpsIndex) => (
                          <div
                            key={`${chatOpsChannel.name}-${chatOpsIndex}`}
                            className={cx({ 'u-margin-right-xs': chatOpsIndex !== chatOpsAvailableChannels.length })}
                          >
                            <Icon name={chatOpsChannel.icon} className={cx('icon')} />
                            <Text type="primary">{chatOpsChannel.name}</Text>
                          </div>
                        )
                      )}
                    </HorizontalGroup>
                  </div>
                )}

                <div className={cx('collapsedRoute__item')}>
                  <div className={cx('u-flex', 'u-align-items-center', 'u-flex-gap-xs')}>
                    <Icon name="list-ui-alt" />
                    <Text type="secondary" className={cx('u-margin-right-xs')}>
                      Trigger escalation chain
                    </Text>
                  </div>

                  {escalationChain?.name && (
                    <PluginLink
                      className={cx('hover-button')}
                      target="_blank"
                      query={{ page: 'escalations', id: channelFilter.escalation_chain }}
                    >
                      <Text type="primary">{escalationChain?.name}</Text>
                    </PluginLink>
                  )}

                  {!escalationChain?.name && (
                    <div className={cx('u-flex', 'u-align-items-center', 'u-flex-gap-xs')}>
                      <div className={cx('icon-exclamation')}>
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
      await alertReceiveChannelStore.deleteChannelFilter(routeIdForDeletion);
      openNotification('Route has been deleted');
    }
  }
);

export default CollapsedIntegrationRouteDisplay;
