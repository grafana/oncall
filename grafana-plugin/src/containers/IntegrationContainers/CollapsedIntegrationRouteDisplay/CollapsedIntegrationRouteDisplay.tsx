import React, { useEffect, useState } from 'react';

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
import IntegrationHelper from 'pages/integration_2/Integration2.helper';
import { useStore } from 'state/useStore';

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
    const { escalationChainStore, alertReceiveChannelStore, telegramChannelStore } = store;
    const [routeIdForDeletion, setRouteIdForDeletion] = useState<ChannelFilter['id']>(undefined);
    const [telegramInfo, setTelegramInfo] = useState<Array<{ id: string; channel_name: string }>>([]);

    useEffect(() => {
      (async function () {
        const telegram = await telegramChannelStore.getAll();
        setTelegramInfo(telegram);
      })();
    }, [channelFilterId]);

    const channelFilter = alertReceiveChannelStore.channelFilters[channelFilterId];
    if (!channelFilter) {
      return null;
    }

    const escalationChain = escalationChainStore.items[channelFilter.escalation_chain];
    const routeWording = IntegrationHelper.getRouteConditionWording(
      alertReceiveChannelStore.channelFilterIds[alertReceiveChannelId],
      routeIndex
    );

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
                  text={IntegrationHelper.getRouteConditionWording(
                    alertReceiveChannelStore.channelFilterIds[alertReceiveChannelId],
                    routeIndex
                  )}
                  tooltipTitle={IntegrationHelper.getRouteConditionTooltipWording(
                    alertReceiveChannelStore.channelFilterIds[alertReceiveChannelId],
                    routeIndex
                  )}
                  tooltipContent={undefined}
                />
                {routeWording === 'Default' && (
                  <Text type="primary">All unrouted routes will be served to the default route</Text>
                )}
                {routeWording !== 'Default' && channelFilter.filtering_term && (
                  <Text type="primary" className={cx('heading-container__text')}>
                    {channelFilter.filtering_term}
                  </Text>
                )}
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
                {IntegrationHelper.getChatOpsChannels(channelFilter, telegramInfo, store)
                  .filter((it) => it)
                  .map((chatOpsChannel, key) => (
                    <HorizontalGroup key={key}>
                      <Text type="secondary">Publish to ChatOps</Text>
                      <Icon name={chatOpsChannel.icon} />
                      <Text type="primary" strong>
                        {chatOpsChannel.name}
                      </Text>
                    </HorizontalGroup>
                  ))}

                <HorizontalGroup>
                  <Icon name="list-ui-alt" />
                  <Text type="secondary">Trigger escalation chain:</Text>

                  {escalationChain?.name && (
                    <PluginLink
                      className={cx('hover-button')}
                      target="_blank"
                      query={{ page: 'escalations', id: channelFilter.escalation_chain }}
                    >
                      <Text type="primary" strong>
                        {escalationChain?.name}
                      </Text>
                    </PluginLink>
                  )}

                  {!escalationChain?.name && (
                    <HorizontalGroup spacing={'xs'}>
                      <div className={cx('icon-exclamation')}>
                        <Icon name="exclamation-triangle" />
                      </div>
                      <Text type="primary">No Escalation chain selected</Text>
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
    }
  }
);

export default CollapsedIntegrationRouteDisplay;
