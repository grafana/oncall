import React, { useState } from 'react';

import { ConfirmModal, HorizontalGroup, Icon } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import PluginLink from 'components/PluginLink/PluginLink';
import Tag from 'components/Tag/Tag';
import Text from 'components/Text/Text';
import { AlertReceiveChannel } from 'models/alert_receive_channel';
import { ChannelFilter } from 'models/channel_filter';
import { useStore } from 'state/useStore';
import { getVar } from 'utils/DOM';

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
          hasCollapsedBorder
          key={channelFilterId}
          heading={
            <HorizontalGroup justify={'space-between'}>
              <HorizontalGroup spacing={'md'}>
                <Tag color={getVar('--tag-primary')}>
                  {IntegrationHelper.getRouteConditionWording(alertReceiveChannelStore.channelFilters, routeIndex)}
                </Tag>
                {channelFilter.filtering_term && (
                  <Text type="link">{IntegrationHelper.truncateLine(channelFilter.filtering_term)}</Text>
                )}
              </HorizontalGroup>
              <HorizontalGroup>
                <RouteButtonsDisplay
                  alertReceiveChannelId={alertReceiveChannelId}
                  channelFilterId={channelFilterId}
                  routeIndex={routeIndex}
                  setRouteIdForDeletion={() => setRouteIdForDeletion(channelFilterId)}
                />
              </HorizontalGroup>
            </HorizontalGroup>
          }
          content={
            <div className={cx('spacing')}>
              <HorizontalGroup>
                {channelFilter.slack_channel?.display_name && (
                  <HorizontalGroup>
                    <Text type="secondary">Publish to ChatOps</Text>
                    <Icon name="slack" />
                    <Text type="primary" strong>
                      {channelFilter.slack_channel.display_name}
                    </Text>
                  </HorizontalGroup>
                )}
                <HorizontalGroup>
                  <Icon name="list-ui-alt" />
                  <Text type="secondary">Escalate to</Text>
                  <PluginLink
                    className={cx('hover-button')}
                    target="_blank"
                    query={{ page: 'escalations', id: channelFilter.escalation_chain }}
                  >
                    <Text type="primary" strong>
                      {escalationChain?.name}
                    </Text>
                  </PluginLink>
                </HorizontalGroup>
              </HorizontalGroup>
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
