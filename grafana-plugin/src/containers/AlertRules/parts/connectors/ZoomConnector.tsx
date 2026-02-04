import React, { useCallback } from 'react';

import { cx } from '@emotion/css';
import { InlineSwitch, Stack, useStyles2 } from '@grafana/ui';
import { UserActions } from 'helpers/authorization/authorization';
import { StackSize } from 'helpers/consts';
import { observer } from 'mobx-react';

import { GSelect } from 'containers/GSelect/GSelect';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { ChannelFilter } from 'models/channel_filter/channel_filter.types';
import { ZoomChannel } from 'models/zoom/zoom.types';
import { useStore } from 'state/useStore';

import { getConnectorsStyles } from './Connectors.styles';

interface ZoomConnectorProps {
  channelFilterId: ChannelFilter['id'];
}

export const ZoomConnector = observer((props: ZoomConnectorProps) => {
  const { channelFilterId } = props;

  const store = useStore();
  const styles = useStyles2(getConnectorsStyles);

  const {
    alertReceiveChannelStore,
    zoomChannelStore,
    // dereferencing items is needed to rerender GSelect
    zoomChannelStore: { items: zoomChannelItems },
  } = store;

  const channelFilter = alertReceiveChannelStore.channelFilters[channelFilterId];

  const handleZoomChannelChange = useCallback(
    (_value: ZoomChannel['id'], zoomChannel: ZoomChannel) => {
      alertReceiveChannelStore.saveChannelFilter(channelFilterId, {
        notification_backends: {
          ZOOM: { channel: zoomChannel?.id || null },
        },
      });
    },
    [alertReceiveChannelStore, channelFilterId]
  );

  const handleChannelFilterNotifyInZoomChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      alertReceiveChannelStore.saveChannelFilter(channelFilterId, {
        notification_backends: { ZOOM: { enabled: event.target.checked } },
      });
    },
    [alertReceiveChannelStore, channelFilterId]
  );

  return (
    <div className={styles.root}>
      <Stack wrap="wrap" gap={StackSize.sm}>
        <div>
          <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
            <InlineSwitch
              value={channelFilter.notification_backends?.ZOOM?.enabled}
              onChange={handleChannelFilterNotifyInZoomChange}
              transparent
            />
          </WithPermissionControlTooltip>
        </div>
        Post to Zoom channel
        <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
          <GSelect<ZoomChannel>
            allowClear
            className={cx('select', 'control')}
            items={zoomChannelItems}
            fetchItemsFn={zoomChannelStore.updateItems}
            fetchItemFn={zoomChannelStore.updateById}
            getSearchResult={zoomChannelStore.getSearchResult}
            displayField="channel_name"
            valueField="id"
            placeholder="Select Zoom Channel"
            value={channelFilter.notification_backends?.ZOOM?.channel}
            onChange={handleZoomChannelChange}
          />
        </WithPermissionControlTooltip>
      </Stack>
    </div>
  );
});
