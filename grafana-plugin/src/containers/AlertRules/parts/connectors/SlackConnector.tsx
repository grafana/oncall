import React, { useCallback } from 'react';

import { cx } from '@emotion/css';
import { InlineSwitch, Stack, useStyles2 } from '@grafana/ui';
import { UserActions } from 'helpers/authorization/authorization';
import { StackSize } from 'helpers/consts';
import { observer } from 'mobx-react';

import { GSelect } from 'containers/GSelect/GSelect';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { ChannelFilter } from 'models/channel_filter/channel_filter.types';
import { PRIVATE_CHANNEL_NAME } from 'models/slack_channel/slack_channel.config';
import { SlackChannel } from 'models/slack_channel/slack_channel.types';
import { useStore } from 'state/useStore';

import { getConnectorsStyles } from './Connectors.styles';

interface SlackConnectorProps {
  channelFilterId: ChannelFilter['id'];
}

export const SlackConnector = observer((props: SlackConnectorProps) => {
  const { channelFilterId } = props;

  const store = useStore();
  const styles = useStyles2(getConnectorsStyles);

  const {
    organizationStore: { currentOrganization },
    alertReceiveChannelStore,
    slackChannelStore,
    // dereferencing items is needed to rerender GSelect
    slackChannelStore: { items: slackChannelItems },
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
    <div className={styles.root}>
      <Stack wrap="wrap" gap={StackSize.sm}>
        <div>
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
            allowClear
            className={cx('select', 'control')}
            items={slackChannelItems}
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
      </Stack>
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
});
