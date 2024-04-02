import React, { useCallback } from 'react';

import { HorizontalGroup, InlineSwitch } from '@grafana/ui';
import cn from 'classnames/bind';

import { GSelect } from 'containers/GSelect/GSelect';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { ChannelFilter } from 'models/channel_filter/channel_filter.types';
import { PRIVATE_CHANNEL_NAME } from 'models/slack_channel/slack_channel.config';
import { SlackChannel } from 'models/slack_channel/slack_channel.types';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization/authorization';

import styles from './Connectors.module.css';

const cx = cn.bind(styles);

interface SlackConnectorProps {
  channelFilterId: ChannelFilter['id'];
}

export const SlackConnector = (props: SlackConnectorProps) => {
  const { channelFilterId } = props;

  const store = useStore();
  const {
    organizationStore: { currentOrganization },
    alertReceiveChannelStore,
    slackChannelStore,
  } = store;

  const channelFilter = store.alertReceiveChannelStore.channelFilters[channelFilterId];

  const handleSlackChannelChange = useCallback((_value: SlackChannel['id'], slackChannel: SlackChannel) => {
    // @ts-ignore actually slack_channel is just slack_channel_id when saving
    alertReceiveChannelStore.saveChannelFilter(channelFilterId, { slack_channel: slackChannel?.slack_id || null });
  }, []);

  const handleChannelFilterNotifyInSlackChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    alertReceiveChannelStore.saveChannelFilter(channelFilterId, { notify_in_slack: event.target.checked });
  }, []);

  return (
    <div className={cx('root')}>
      <HorizontalGroup wrap spacing="sm">
        <div className={cx('slack-channel-switch')}>
          <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
            <InlineSwitch
              value={channelFilter.notify_in_slack}
              onChange={handleChannelFilterNotifyInSlackChange}
              transparent
            />
          </WithPermissionControlTooltip>
        </div>
        Slack Channel
        <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
          <GSelect<SlackChannel>
            showSearch
            allowClear
            className={cx('select', 'control')}
            items={slackChannelStore.items}
            fetchItemsFn={slackChannelStore.updateItems}
            fetchItemFn={slackChannelStore.updateItem}
            getSearchResult={getSearchResult}
            displayField="display_name"
            valueField="id"
            placeholder="Select Slack Channel"
            value={channelFilter.slack_channel?.id || currentOrganization?.slack_channel?.id}
            // prevent showing it as General (Default) when already selected
            parseDisplayName={(label) => label.replace(` (Default)`, '')}
            onChange={handleSlackChannelChange}
            nullItemName={PRIVATE_CHANNEL_NAME}
          />
        </WithPermissionControlTooltip>
      </HorizontalGroup>
    </div>
  );

  function getSearchResult(query = ''): SlackChannel[] {
    const results = slackChannelStore.getSearchResult(query);
    const defaultChannelId = currentOrganization?.slack_channel?.id;

    if (defaultChannelId) {
      // if there's any default channel id, put it first in the list
      const defaultChannel = results.find((res) => res.id === defaultChannelId);
      const newList = results.filter((channel) => channel.id !== defaultChannelId);

      if (defaultChannel) {
        defaultChannel.display_name += ` (Default)`;
        newList.unshift(defaultChannel);
      }

      return newList;
    }

    return results;
  }
};
