import React from 'react';

import { Badge, HorizontalGroup, IconButton, Tooltip, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import CopyToClipboard from 'react-copy-to-clipboard';
import Emoji from 'react-emoji-render';

import IntegrationLogo from 'components/IntegrationLogo/IntegrationLogo';
import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import TeamName from 'containers/TeamName/TeamName';
import { HeartGreenIcon, HeartRedIcon } from 'icons';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { useStore } from 'state/useStore';

import styles from './AlertReceiveChannelCard.module.scss';

const cx = cn.bind(styles);

interface AlertReceiveChannelCardProps {
  id: AlertReceiveChannel['id'];
  onShowHeartbeatModal: () => void;
}

const AlertReceiveChannelCard = observer((props: AlertReceiveChannelCardProps) => {
  const { id, onShowHeartbeatModal } = props;

  const store = useStore();

  const { alertReceiveChannelStore, heartbeatStore, grafanaTeamStore } = store;

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
          <HorizontalGroup>
            <Text type="primary" size="medium">
              <Emoji className={cx('title')} text={alertReceiveChannel.verbal_name} />
            </Text>
            <CopyToClipboard text={alertReceiveChannel.id}>
              <IconButton
                variant="primary"
                tooltip={
                  <div>
                    ID {alertReceiveChannel.id}
                    <br />
                    (click to copy ID to clipboard)
                  </div>
                }
                tooltipPlacement="top"
                name="info-circle"
              />
            </CopyToClipboard>
            {alertReceiveChannelCounter && (
              <PluginLink
                query={{ page: 'alert-groups', integration: alertReceiveChannel.id }}
                className={cx('alertsInfoText')}
              >
                <Badge
                  text={alertReceiveChannelCounter?.alerts_count + '/' + alertReceiveChannelCounter?.alert_groups_count}
                  color={'blue'}
                  tooltip={
                    alertReceiveChannelCounter?.alerts_count +
                    ' alert' +
                    (alertReceiveChannelCounter?.alerts_count === 1 ? '' : 's') +
                    ' in ' +
                    alertReceiveChannelCounter?.alert_groups_count +
                    ' alert group' +
                    (alertReceiveChannelCounter?.alert_groups_count === 1 ? '' : 's')
                  }
                />
              </PluginLink>
            )}
          </HorizontalGroup>
          <HorizontalGroup spacing="xs">
            <IntegrationLogo scale={0.08} integration={integration} />
            <Text type="secondary" size="small">
              {integration?.display_name}
            </Text>
          </HorizontalGroup>
          <TeamName team={grafanaTeamStore.items[alertReceiveChannel.team]} size="small" />
        </VerticalGroup>
      </HorizontalGroup>
    </div>
  );
});

export default AlertReceiveChannelCard;
