import React, { useCallback } from 'react';

import { cx } from '@emotion/css';
import { InlineSwitch, Stack, useStyles2 } from '@grafana/ui';
import { UserActions } from 'helpers/authorization/authorization';
import { StackSize } from 'helpers/consts';
import { observer } from 'mobx-react';

import { GSelect } from 'containers/GSelect/GSelect';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { ChannelFilter } from 'models/channel_filter/channel_filter.types';
import { TelegramChannel } from 'models/telegram_channel/telegram_channel.types';
import { useStore } from 'state/useStore';

import { getConnectorsStyles } from './Connectors.styles';

interface TelegramConnectorProps {
  channelFilterId: ChannelFilter['id'];
}

export const TelegramConnector = observer(({ channelFilterId }: TelegramConnectorProps) => {
  const store = useStore();
  const styles = useStyles2(getConnectorsStyles);

  const {
    alertReceiveChannelStore,
    telegramChannelStore,
    // dereferencing items is needed to rerender GSelect
    telegramChannelStore: { items: telegramChannelItems },
  } = store;

  const channelFilter = store.alertReceiveChannelStore.channelFilters[channelFilterId];

  const handleTelegramChannelChange = useCallback((_value: TelegramChannel['id'], telegramChannel: TelegramChannel) => {
    alertReceiveChannelStore.saveChannelFilter(channelFilterId, { telegram_channel: telegramChannel?.id || null });
  }, []);

  const handleChannelFilterNotifyInTelegramChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    alertReceiveChannelStore.saveChannelFilter(channelFilterId, { notify_in_telegram: event.target.checked });
  }, []);

  return (
    <div className={styles.root}>
      <Stack wrap="wrap" gap={StackSize.sm}>
        <div>
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
          <GSelect<TelegramChannel>
            allowClear
            className={cx('select', 'control')}
            items={telegramChannelItems}
            fetchItemsFn={telegramChannelStore.updateItems}
            fetchItemFn={telegramChannelStore.updateById}
            getSearchResult={telegramChannelStore.getSearchResult}
            displayField="channel_name"
            valueField="id"
            placeholder="Select Telegram Channel"
            value={channelFilter.telegram_channel}
            onChange={handleTelegramChannelChange}
          />
        </WithPermissionControlTooltip>
      </Stack>
    </div>
  );
});
