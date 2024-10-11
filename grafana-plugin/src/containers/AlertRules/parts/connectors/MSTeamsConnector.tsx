import React, { useCallback } from 'react';

import { cx } from '@emotion/css';
import { InlineSwitch, Stack, useStyles2 } from '@grafana/ui';
import { UserActions } from 'helpers/authorization/authorization';
import { StackSize } from 'helpers/consts';
import { observer } from 'mobx-react';

import { GSelect } from 'containers/GSelect/GSelect';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { ChannelFilter } from 'models/channel_filter/channel_filter.types';
import { MSTeamsChannel } from 'models/msteams_channel/msteams_channel.types';
import { useStore } from 'state/useStore';

import { getConnectorsStyles } from './Connectors.styles';

interface MSTeamsConnectorProps {
  channelFilterId: ChannelFilter['id'];
}

export const MSTeamsConnector = observer((props: MSTeamsConnectorProps) => {
  const { channelFilterId } = props;

  const store = useStore();
  const styles = useStyles2(getConnectorsStyles);

  const {
    alertReceiveChannelStore,
    msteamsChannelStore,
    // dereferencing items is needed to rerender GSelect
    msteamsChannelStore: { items: msteamsChannelItems },
  } = store;

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
    <div className={styles.root}>
      <Stack wrap="wrap" gap={StackSize.sm}>
        <div>
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
            allowClear
            className={cx('select', 'control')}
            items={msteamsChannelItems}
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
      </Stack>
    </div>
  );
});
