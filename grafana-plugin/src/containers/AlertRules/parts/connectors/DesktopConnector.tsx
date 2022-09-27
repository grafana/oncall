import React, { useCallback } from 'react';

import { HorizontalGroup, InlineSwitch } from '@grafana/ui';
import cn from 'classnames/bind';

import GSelect from 'containers/GSelect/GSelect';
import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { ChannelFilter } from 'models/channel_filter/channel_filter.types';
import { DesktopChannel } from 'models/desktop_channel/desktop_channel.types';
import { useStore } from 'state/useStore';
import { UserAction } from 'state/userAction';

import styles from 'containers/AlertRules/parts/connectors/index.module.css';

const cx = cn.bind(styles);

interface DesktopConnectorProps {
  channelFilterId: ChannelFilter['id'];
}

const DesktopConnector = (props: DesktopConnectorProps) => {
  const { channelFilterId } = props;

  const store = useStore();
  const { teamStore, alertReceiveChannelStore } = store;

  const channelFilter = store.alertReceiveChannelStore.channelFilters[channelFilterId];

  const handleDesktopChannelChange = useCallback((value: DesktopChannel['id'], channel: DesktopChannel) => {
    alertReceiveChannelStore.saveChannelFilter(channelFilterId, { notification_backends: { DESKTOPDEMO: { channel: channel?.id || null } } });
  }, []);

  const handleChannelFilterNotifyInDesktopChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    alertReceiveChannelStore.saveChannelFilter(channelFilterId, { notification_backends: { DESKTOPDEMO: { enabled: event.target.checked } } });
  }, []);


  return (
    <div className={cx('root')}>
      <HorizontalGroup wrap spacing="sm">
          <div className={cx('slack-channel-switch')}>
            <WithPermissionControl userAction={UserAction.UpdateAlertReceiveChannels}>
              <InlineSwitch
                value={channelFilter.notification_backends?.DESKTOPDEMO?.enabled}
                onChange={handleChannelFilterNotifyInDesktopChange}
                transparent
              />
            </WithPermissionControl>
          </div>
          Post to Desktop
          <WithPermissionControl userAction={UserAction.UpdateAlertReceiveChannels}>
            <GSelect
              showSearch
              allowClear
              className={cx('select', 'control')}
              modelName="desktopChannelStore"
              displayField="name"
              valueField="id"
              placeholder="Select Channel"
              value={channelFilter.notification_backends?.DESKTOPDEMO?.channel}
              onChange={handleDesktopChannelChange}
            />
          </WithPermissionControl>
      </HorizontalGroup>
    </div>
  );
};

export default DesktopConnector;
