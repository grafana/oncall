import React, { useCallback } from 'react';

import { HorizontalGroup, InlineSwitch } from '@grafana/ui';
import cn from 'classnames/bind';

import GSelect from 'containers/GSelect/GSelect';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { ChannelFilter } from 'models/channel_filter/channel_filter.types';
import { TelegramChannel } from 'models/telegram_channel/telegram_channel.types';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization';

import styles from './index.module.css';

const cx = cn.bind(styles);

interface TelegramConnectorProps {
  channelFilterId: ChannelFilter['id'];
}

const TelegramConnector = ({ channelFilterId }: TelegramConnectorProps) => {
  const store = useStore();
  const { alertReceiveChannelStore } = store;

  const channelFilter = store.alertReceiveChannelStore.channelFilters[channelFilterId];

  const handleTelegramChannelChange = useCallback((_value: TelegramChannel['id'], telegramChannel: TelegramChannel) => {
    alertReceiveChannelStore.saveChannelFilter(channelFilterId, { telegram_channel: telegramChannel?.id || null });
  }, []);

  const handleChannelFilterNotifyInTelegramChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    alertReceiveChannelStore.saveChannelFilter(channelFilterId, { notify_in_telegram: event.target.checked });
  }, []);

  return (
    <div className={cx('root')}>
      <HorizontalGroup wrap spacing="sm">
        <div className={cx('slack-channel-switch')}>
          <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
            <InlineSwitch
              value={channelFilter.notify_in_telegram}
              onChange={handleChannelFilterNotifyInTelegramChange}
              transparent
            />
          </WithPermissionControlTooltip>
        </div>
        Post to telegram channel
        <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
          <GSelect
            showSearch
            allowClear
            className={cx('select', 'control')}
            modelName="telegramChannelStore"
            displayField="channel_name"
            valueField="id"
            placeholder="Select Telegram Channel"
            value={channelFilter.telegram_channel}
            onChange={handleTelegramChannelChange}
          />
        </WithPermissionControlTooltip>
      </HorizontalGroup>
    </div>
  );
};

export default TelegramConnector;
