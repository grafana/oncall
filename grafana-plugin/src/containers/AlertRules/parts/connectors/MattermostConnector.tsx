import React, { useCallback } from 'react';

import { HorizontalGroup, InlineSwitch } from '@grafana/ui';
import cn from 'classnames/bind';

import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { ChannelFilter } from 'models/channel_filter/channel_filter.types';
import { useStore } from 'state/useStore';
import { UserAction } from 'state/userAction';

import styles from 'containers/AlertRules/parts/connectors/index.module.css';

const cx = cn.bind(styles);

interface MattermostConnectorProps {
  channelFilterId: ChannelFilter['id'];
}

const MattermostConnector = (props: MattermostConnectorProps) => {
  const { channelFilterId } = props;

  const store = useStore();
  const { alertReceiveChannelStore } = store;

  const channelFilter = store.alertReceiveChannelStore.channelFilters[channelFilterId];

  const handleChannelFilterNotifyInMattermostChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    alertReceiveChannelStore.saveChannelFilter(channelFilterId, { notification_backends: { MATTERMOST: { enabled: event.target.checked } } });
  }, []);


  return (
    <div className={cx('root')}>
      <HorizontalGroup wrap spacing="sm">
          <div className={cx('slack-channel-switch')}>
            <WithPermissionControl userAction={UserAction.UpdateAlertReceiveChannels}>
              <InlineSwitch
                value={channelFilter.notification_backends?.MATTERMOST?.enabled}
                onChange={handleChannelFilterNotifyInMattermostChange}
                transparent
              />
            </WithPermissionControl>
          </div>
          Post to Mattermost
      </HorizontalGroup>
    </div>
  );
};

export default MattermostConnector;
