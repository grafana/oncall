import React from 'react';
import IntegrationBlock from './IntegrationBlock';
import { observer } from 'mobx-react';
import { HorizontalGroup, Icon } from '@grafana/ui';
import Tag from 'components/Tag/Tag';
import { getVar } from 'utils/DOM';
import { useStore } from 'state/useStore';
import IntegrationHelper from './Integration2.helper';
import { ChannelFilter } from 'models/channel_filter';
import Text from 'components/Text/Text';

interface CollapsedIntegrationRouteDisplayProps {
  channelFilterId: ChannelFilter['id'];
  routeIndex: number;
}

const CollapsedIntegrationRouteDisplay: React.FC<CollapsedIntegrationRouteDisplayProps> = observer(
  ({ channelFilterId, routeIndex }) => {
    const { alertReceiveChannelStore } = useStore();
    const channelFilter = alertReceiveChannelStore.channelFilters[channelFilterId];

    return (
      <IntegrationBlock
      hasCollapsedBorder
        heading={
          <HorizontalGroup justify={'space-between'}>
            <HorizontalGroup spacing={'md'}>
              <Tag color={getVar('--tag-primary')}>
                {IntegrationHelper.getRouteConditionWording(alertReceiveChannelStore.channelFilters, routeIndex)}
              </Tag>
              {channelFilter.filtering_term && <Text type="secondary">{channelFilter.filtering_term}</Text>}
            </HorizontalGroup>
          </HorizontalGroup>
        }
        content={
          <HorizontalGroup>
            <HorizontalGroup>
              <Text type="secondary">Publish to ChatOps</Text>
              <Icon name="slack" />
            </HorizontalGroup>
            <HorizontalGroup>
              <Icon name="list-ui-alt" />
              <Text type="secondary">Escalate to</Text>
            </HorizontalGroup>
          </HorizontalGroup>
        }
      />
    );
  }
);

export default CollapsedIntegrationRouteDisplay;
