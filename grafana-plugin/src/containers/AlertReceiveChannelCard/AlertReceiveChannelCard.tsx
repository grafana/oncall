import React from 'react';

import { Tooltip, HorizontalGroup, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import Emoji from 'react-emoji-render';

import IntegrationLogo from 'components/IntegrationLogo/IntegrationLogo';
import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import { HeartGreenIcon, HeartRedIcon } from 'icons';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { useStore } from 'state/useStore';

import styles from './AlertReceiveChannelCard.module.css';

const cx = cn.bind(styles);

interface AlertReceiveChannelCardProps {
  id: AlertReceiveChannel['id'];
  onShowHeartbeatModal: () => void;
}

const AlertReceiveChannelCard = observer((props: AlertReceiveChannelCardProps) => {
  const { id, onShowHeartbeatModal } = props;

  const store = useStore();

  const { alertReceiveChannelStore, heartbeatStore } = store;

  const alertReceiveChannel = alertReceiveChannelStore.items[id];
  const alertReceiveChannelCounter = alertReceiveChannelStore.counters[id];

  const heartbeatId = alertReceiveChannelStore.alertReceiveChannelToHeartbeat[alertReceiveChannel.id];
  const heartbeat = heartbeatStore.items[heartbeatId];

  const heartbeatStatus = Boolean(heartbeat?.status);

  const integration = alertReceiveChannelStore.getIntegration(alertReceiveChannel);

  return (
    <div className={cx('root')}>
      <HorizontalGroup align="flex-start">
        <div className={cx('heartbeat')}>
          {alertReceiveChannel.is_available_for_integration_heartbeat && (
            <Tooltip
              placement="top"
              content={
                heartbeat
                  ? `Last heartbeat: ${heartbeat.last_heartbeat_time_verbal || 'never'}`
                  : 'Click to setup heartbeat'
              }
            >
              <div className={cx('heartbeat-icon')} onClick={onShowHeartbeatModal}>
                {heartbeatStatus ? <HeartGreenIcon /> : <HeartRedIcon />}
              </div>
            </Tooltip>
          )}
        </div>
        <VerticalGroup spacing="xs">
          <Text type="primary" size="medium">
            <Emoji className={cx('title')} text={alertReceiveChannel.verbal_name} />
          </Text>

          <HorizontalGroup>
            <IntegrationLogo scale={0.08} integration={integration} />
            <Text type="secondary" size="small">
              {integration?.display_name}
            </Text>
            <Text type="secondary" size="small">
              |
            </Text>
            {alertReceiveChannelCounter && (
              <PluginLink
                query={{ page: 'incidents', integration: alertReceiveChannel.id }}
                className={cx('alertsInfoText')}
              >
                <b>{alertReceiveChannelCounter?.alerts_count}</b> alert
                {alertReceiveChannelCounter?.alerts_count === 1 ? '' : 's'} in{' '}
                <b>{alertReceiveChannelCounter?.alert_groups_count}</b> Alert Group
                {alertReceiveChannelCounter?.alert_groups_count === 1 ? '' : 's'}
              </PluginLink>
            )}
          </HorizontalGroup>
        </VerticalGroup>
      </HorizontalGroup>
    </div>
  );
});

export default AlertReceiveChannelCard;
