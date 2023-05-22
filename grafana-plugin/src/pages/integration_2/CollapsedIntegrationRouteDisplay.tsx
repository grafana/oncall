import React, { useState } from 'react';

import { ConfirmModal, HorizontalGroup, Icon, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import TooltipBadge from 'components/TooltipBadge/TooltipBadge';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { ChannelFilter } from 'models/channel_filter';
import { useStore } from 'state/useStore';

import styles from './CollapsedIntegrationRouteDisplay.module.scss';
import { RouteButtonsDisplay } from './ExpandedIntegrationRouteDisplay';
import IntegrationHelper from './Integration2.helper';
import IntegrationBlock from './IntegrationBlock';

const cx = cn.bind(styles);

interface CollapsedIntegrationRouteDisplayProps {
  alertReceiveChannelId: AlertReceiveChannel['id'];
  channelFilterId: ChannelFilter['id'];
  routeIndex: number;
}

const CollapsedIntegrationRouteDisplay: React.FC<CollapsedIntegrationRouteDisplayProps> = observer(
  ({ channelFilterId, alertReceiveChannelId, routeIndex }) => {
    const { escalationChainStore, alertReceiveChannelStore } = useStore();
    const [routeIdForDeletion, setRouteIdForDeletion] = useState<ChannelFilter['id']>(undefined);

    const channelFilter = alertReceiveChannelStore.channelFilters[channelFilterId];
    if (!channelFilter) {
      return null;
    }

    const escalationChain = escalationChainStore.items[channelFilter.escalation_chain];

    return (
      <>
        <IntegrationBlock
          hasCollapsedBorder={false}
          key={channelFilterId}
          heading={
            <div className={cx('heading-container')}>
              <div className={cx('heading-container__item', 'heading-container__item--large')}>
                <TooltipBadge
                  borderType="success"
                  text={IntegrationHelper.getRouteConditionWording(
                    alertReceiveChannelStore.channelFilterIds[alertReceiveChannelId],
                    routeIndex
                  )}
                  tooltipTitle={undefined}
                  tooltipContent={undefined}
                />
                {channelFilter.filtering_term && (
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
                {IntegrationHelper.getChatOpsChannels(channelFilter).map((chatOpsChannel) => (
                  <HorizontalGroup>
                    <Text type="secondary">Publish to ChatOps</Text>
                    <Icon name="slack" />
                    <Text type="primary" strong>
                      {chatOpsChannel}
                    </Text>
                  </HorizontalGroup>
                ))}

                <HorizontalGroup>
                  <Icon name="list-ui-alt" />
                  <Text type="secondary">Escalate to</Text>

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
                      <Text type="primary" strong>
                        No Escalation chain
                      </Text>
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
