import React, { useCallback } from 'react';

import { cx } from '@emotion/css';
import { InlineSwitch, Stack, useStyles2 } from '@grafana/ui';
import { UserActions } from 'helpers/authorization/authorization';
import { StackSize } from 'helpers/consts';
import { observer } from 'mobx-react';

import { GSelect } from 'containers/GSelect/GSelect';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { ChannelFilter } from 'models/channel_filter/channel_filter.types';
import { MattermostChannel } from 'models/mattermost/mattermost.types';
import { useStore } from 'state/useStore';

import { getConnectorsStyles } from './Connectors.styles';

interface MattermostConnectorProps {
  channelFilterId: ChannelFilter['id'];
}

export const MattermostConnector = observer((props: MattermostConnectorProps) => {
  const { channelFilterId } = props;

  const store = useStore();
  const styles = useStyles2(getConnectorsStyles);

  const {
    alertReceiveChannelStore,
    mattermostChannelStore,
    // dereferencing items is needed to rerender GSelect
    mattermostChannelStore: { items: mattermostChannelItems },
  } = store;

  const channelFilter = alertReceiveChannelStore.channelFilters[channelFilterId];

  const handleMattermostChannelChange = useCallback((_value: MattermostChannel['id'], mattermostChannel: MattermostChannel) => {
    alertReceiveChannelStore.saveChannelFilter(channelFilterId, {
      notification_backends: {
        MATTERMOST: { channel: mattermostChannel?.id || null },
      },
    });
  }, []);

  const handleChannelFilterNotifyInMattermostChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    alertReceiveChannelStore.saveChannelFilter(channelFilterId, {
      notification_backends: { MATTERMOST: { enabled: event.target.checked } },
    });
  }, []);

  return (
    <div className={styles.root}>
      <Stack wrap="wrap" gap={StackSize.sm}>
        <div>
          <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
            <InlineSwitch
              value={channelFilter.notification_backends?.MATTERMOST?.enabled}
              onChange={handleChannelFilterNotifyInMattermostChange}
              transparent
            />
          </WithPermissionControlTooltip>
        </div>
        Post to Mattermost channel
        <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
          <GSelect<MattermostChannel>
            allowClear
            className={cx('select', 'control')}
            items={mattermostChannelItems}
            fetchItemsFn={mattermostChannelStore.updateItems}
            fetchItemFn={mattermostChannelStore.updateById}
            getSearchResult={mattermostChannelStore.getSearchResult}
            displayField="display_name"
            valueField="id"
            placeholder="Select Mattermost Channel"
            value={channelFilter.notification_backends?.MATTERMOST?.channel}
            onChange={handleMattermostChannelChange}
          />
        </WithPermissionControlTooltip>
      </Stack>
    </div>
  );
});
