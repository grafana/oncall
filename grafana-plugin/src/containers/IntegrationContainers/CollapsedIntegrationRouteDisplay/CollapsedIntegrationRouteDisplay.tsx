import React, { useState } from 'react';

import { ConfirmModal, HorizontalGroup, Icon, VerticalGroup } from '@grafana/ui';
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
import CommonIntegrationHelper from 'pages/integration_2/CommonIntegration2.helper';
import IntegrationHelper from 'pages/integration_2/Integration2.helper';
import { useStore } from 'state/useStore';
import { openNotification } from 'utils';

const cx = cn.bind(styles);

interface CollapsedIntegrationRouteDisplayProps {
  alertReceiveChannelId: AlertReceiveChannel['id'];
  channelFilterId: ChannelFilter['id'];
  routeIndex: number;
  toggle: () => void;
}

const CollapsedIntegrationRouteDisplay: React.FC<CollapsedIntegrationRouteDisplayProps> = observer(
  ({ channelFilterId, alertReceiveChannelId, routeIndex, toggle }) => {
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
    const chatOpsAvailableChannels = IntegrationHelper.getChatOpsChannels(channelFilter, store);

    return (
      <>
        <IntegrationBlock
          hasCollapsedBorder={false}
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
                />
              </div>
            </div>
          }
          content={
            <div className={cx('spacing')}>
              <VerticalGroup>
                {chatOpsAvailableChannels.length > 0 && (
                  <HorizontalGroup spacing="xs">
                    <Text type="secondary">Publish to ChatOps</Text>

                    {chatOpsAvailableChannels
                      .filter((it) => it)
                      .map((chatOpsChannel) => (
                        <>
                          <Icon name={chatOpsChannel.icon} />
                          <Text type="primary" strong>
                            {chatOpsChannel.name}
                          </Text>
                        </>
                      ))}
                  </HorizontalGroup>
                )}

                <HorizontalGroup>
                  <HorizontalGroup spacing={'xs'}>
                    <Icon name="list-ui-alt" />
                    <Text type="secondary">Trigger escalation chain</Text>
                  </HorizontalGroup>

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
                    <HorizontalGroup spacing={'xs'}>
                      <div className={cx('icon-exclamation')}>
                        <Icon name="exclamation-triangle" />
                      </div>
                      <Text type="primary">Not selected</Text>
                    </HorizontalGroup>
                  )}
                </HorizontalGroup>
              </VerticalGroup>
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

    async function onRouteDeleteConfirm() {
      setRouteIdForDeletion(undefined);
      await alertReceiveChannelStore.deleteChannelFilter(routeIdForDeletion);
      openNotification('Route has been deleted');
    }
  }
);

export default CollapsedIntegrationRouteDisplay;
