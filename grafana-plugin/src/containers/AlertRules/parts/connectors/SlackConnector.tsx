import React, { useCallback } from 'react';

import { Button, HorizontalGroup, InlineSwitch } from '@grafana/ui';
import cn from 'classnames/bind';

import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import GSelect from 'containers/GSelect/GSelect';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { ChannelFilter } from 'models/channel_filter/channel_filter.types';
import { PRIVATE_CHANNEL_NAME } from 'models/slack_channel/slack_channel.config';
import { getSlackChannelName } from 'models/slack_channel/slack_channel.helpers';
import { SlackChannel } from 'models/slack_channel/slack_channel.types';
import { useStore } from 'state/useStore';
import { isUserActionAllowed, UserActions } from 'utils/authorization';

import styles from './index.module.css';

const cx = cn.bind(styles);

interface SlackConnectorProps {
  channelFilterId: ChannelFilter['id'];
}

const SlackConnector = (props: SlackConnectorProps) => {
  const { channelFilterId } = props;

  const store = useStore();
  const {
    organizationStore: { currentOrganization },
    alertReceiveChannelStore,
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
          <GSelect
            showSearch
            allowClear
            className={cx('select', 'control')}
            modelName="slackChannelStore"
            displayField="display_name"
            valueField="id"
            placeholder="Select Slack Channel"
            value={channelFilter.slack_channel?.id || currentOrganization?.slack_channel?.id}
            onChange={handleSlackChannelChange}
            nullItemName={PRIVATE_CHANNEL_NAME}
          />
        </WithPermissionControlTooltip>
        <HorizontalGroup>
          {Boolean(
            channelFilter.slack_channel?.id &&
              currentOrganization?.slack_channel?.id &&
              channelFilter.slack_channel?.id !== currentOrganization?.slack_channel?.id
          ) ? (
            <Text type="secondary">
              default slack channel is <Text strong>#{getSlackChannelName(currentOrganization?.slack_channel)}</Text>{' '}
              <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
                <Button
                  variant="primary"
                  size="sm"
                  fill="text"
                  onClick={() => {
                    handleSlackChannelChange(
                      currentOrganization?.slack_channel?.id,
                      currentOrganization?.slack_channel
                    );
                  }}
                >
                  Use it here
                </Button>
              </WithPermissionControlTooltip>
            </Text>
          ) : currentOrganization?.slack_channel?.id ? (
            <Text type="secondary">
              This is the default slack channel{' '}
              <PluginLink query={{ page: 'chat-ops' }} disabled={!isUserActionAllowed(UserActions.ChatOpsWrite)}>
                <WithPermissionControlTooltip userAction={UserActions.ChatOpsUpdateSettings}>
                  <Button variant="primary" size="sm" fill="text">
                    Change in Slack settings
                  </Button>
                </WithPermissionControlTooltip>
              </PluginLink>
            </Text>
          ) : null}
        </HorizontalGroup>
      </HorizontalGroup>
    </div>
  );
};

export default SlackConnector;
