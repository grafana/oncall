import React, { useCallback } from 'react';

import { Button, HorizontalGroup, InlineSwitch } from '@grafana/ui';
import cn from 'classnames/bind';

import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import GSelect from 'containers/GSelect/GSelect';
import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { ChannelFilter } from 'models/channel_filter/channel_filter.types';
import { PRIVATE_CHANNEL_NAME } from 'models/slack_channel/slack_channel.config';
import { getSlackChannelName } from 'models/slack_channel/slack_channel.helpers';
import { SlackChannel } from 'models/slack_channel/slack_channel.types';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization';

import styles from './index.module.css';

const cx = cn.bind(styles);

interface SlackConnectorProps {
  channelFilterId: ChannelFilter['id'];
}

const SlackConnector = (props: SlackConnectorProps) => {
  const { channelFilterId } = props;

  const store = useStore();
  const { teamStore, alertReceiveChannelStore } = store;

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
          <WithPermissionControl userAction={UserActions.IntegrationsWrite}>
            <InlineSwitch
              value={channelFilter.notify_in_slack}
              onChange={handleChannelFilterNotifyInSlackChange}
              transparent
            />
          </WithPermissionControl>
        </div>
        Post to slack channel
        <WithPermissionControl userAction={UserActions.IntegrationsWrite}>
          <GSelect
            showSearch
            allowClear
            className={cx('select', 'control')}
            modelName="slackChannelStore"
            displayField="display_name"
            valueField="id"
            placeholder="Select Slack Channel"
            value={channelFilter.slack_channel?.id || teamStore.currentTeam?.slack_channel?.id}
            onChange={handleSlackChannelChange}
            nullItemName={PRIVATE_CHANNEL_NAME}
          />
        </WithPermissionControl>
        <HorizontalGroup>
          {Boolean(
            channelFilter.slack_channel?.id &&
              teamStore.currentTeam?.slack_channel?.id &&
              channelFilter.slack_channel?.id !== teamStore.currentTeam?.slack_channel?.id
          ) ? (
            <Text type="secondary">
              default slack channel is{' '}
              <Text strong>#{getSlackChannelName(store.teamStore.currentTeam?.slack_channel)}</Text>{' '}
              <WithPermissionControl userAction={UserActions.IntegrationsWrite}>
                <Button
                  variant="primary"
                  size="sm"
                  fill="text"
                  onClick={() => {
                    handleSlackChannelChange(
                      teamStore.currentTeam?.slack_channel?.id,
                      teamStore.currentTeam?.slack_channel
                    );
                  }}
                >
                  Use it here
                </Button>
              </WithPermissionControl>
            </Text>
          ) : teamStore.currentTeam?.slack_channel?.id ? (
            <Text type="secondary">
              This is the default slack channel{' '}
              <PluginLink query={{ page: 'chat-ops' }} disabled={!store.isUserActionAllowed(UserActions.ChatOpsWrite)}>
                <WithPermissionControl userAction={UserActions.ChatOpsUpdateSettings}>
                  <Button variant="primary" size="sm" fill="text">
                    Change in Slack settings
                  </Button>
                </WithPermissionControl>
              </PluginLink>
            </Text>
          ) : null}
        </HorizontalGroup>
      </HorizontalGroup>
    </div>
  );
};

export default SlackConnector;
