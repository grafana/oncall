import React, { useCallback } from 'react';

import { HorizontalGroup, InlineSwitch } from '@grafana/ui';
import cn from 'classnames/bind';

import { GSelect } from 'containers/GSelect/GSelect';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { ChannelFilter } from 'models/channel_filter/channel_filter.types';
import { MSTeamsChannel } from 'models/msteams_channel/msteams_channel.types';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization/authorization';

import styles from 'containers/AlertRules/parts/connectors/Connectors.module.css';

const cx = cn.bind(styles);

interface MSTeamsConnectorProps {
  channelFilterId: ChannelFilter['id'];
}

export const MSTeamsConnector = (props: MSTeamsConnectorProps) => {
  const { channelFilterId } = props;

  const store = useStore();
  const { alertReceiveChannelStore, msteamsChannelStore } = store;

  const channelFilter = store.alertReceiveChannelStore.channelFilters[channelFilterId];

  const handleMSTeamsChannelChange = useCallback((_value: MSTeamsChannel['id'], msteamsChannel: MSTeamsChannel) => {
    alertReceiveChannelStore.saveChannelFilter(channelFilterId, {
      notification_backends: {
        MSTEAMS: { channel: msteamsChannel?.id || null },
      },
    });
  }, []);

  const handleChannelFilterNotifyInMSTeamsChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    alertReceiveChannelStore.saveChannelFilter(channelFilterId, {
      notification_backends: { MSTEAMS: { enabled: event.target.checked } },
    });
  }, []);

  return (
    <div className={cx('root')}>
      <HorizontalGroup wrap spacing="sm">
        <div className={cx('slack-channel-switch')}>
          <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
            <InlineSwitch
              value={channelFilter.notification_backends?.MSTEAMS?.enabled}
              onChange={handleChannelFilterNotifyInMSTeamsChange}
              transparent
            />
          </WithPermissionControlTooltip>
        </div>
        Post to Microsoft Teams channel
        <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
          <GSelect<MSTeamsChannel>
            showSearch
            allowClear
            className={cx('select', 'control')}
            items={msteamsChannelStore.items}
            fetchItemsFn={msteamsChannelStore.updateItems}
            fetchItemFn={msteamsChannelStore.updateById}
            getSearchResult={msteamsChannelStore.getSearchResult}
            displayField="display_name"
            valueField="id"
            placeholder="Select Microsoft Teams Channel"
            value={channelFilter.notification_backends?.MSTEAMS?.channel}
            onChange={handleMSTeamsChannelChange}
          />
        </WithPermissionControlTooltip>
      </HorizontalGroup>
    </div>
  );
};
