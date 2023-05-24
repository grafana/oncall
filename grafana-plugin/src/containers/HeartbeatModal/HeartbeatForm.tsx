import React, { useCallback, useEffect, useState } from 'react';

import { SelectableValue } from '@grafana/data';
import { Button, HorizontalGroup, Select } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import Emoji from 'react-emoji-render';

import Text from 'components/Text/Text';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { HeartGreenIcon, HeartRedIcon } from 'icons';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { SelectOption } from 'state/types';
import { useStore } from 'state/useStore';
import { withMobXProviderContext } from 'state/withStore';
import { UserActions } from 'utils/authorization';

import styles from './HeartbeatForm.module.css';

const cx = cn.bind(styles);

interface HeartBeatModalProps {
  alertReceveChannelId: AlertReceiveChannel['id'];
  onUpdate: () => void;
}

const HeartbeatForm = observer(({ alertReceveChannelId, onUpdate }: HeartBeatModalProps) => {
  const store = useStore();
  const { alertReceiveChannelStore, heartbeatStore } = store;
  const [timeout, setTimeoutSeconds] = useState<number | undefined>();

  const alertReceiveChannel = alertReceiveChannelStore.items[alertReceveChannelId];

  const heartbeatId = alertReceiveChannelStore.alertReceiveChannelToHeartbeat[alertReceveChannelId];

  const heartbeat = heartbeatStore.items[heartbeatId];

  useEffect(() => {
    if (heartbeat) {
      setTimeoutSeconds(heartbeat.timeout_seconds);
    }
  }, [heartbeat]);

  useEffect(() => {
    heartbeatStore.updateTimeoutOptions();
  }, [heartbeatStore]);

  const handleOkClick = useCallback(async () => {
    if (heartbeat) {
      await heartbeatStore.saveHeartbeat(heartbeat.id, {
        alert_receive_channel: heartbeat.alert_receive_channel,
        timeout_seconds: timeout,
      });

      onUpdate();
    } else {
      await heartbeatStore.createHeartbeat(alertReceveChannelId, {
        timeout_seconds: timeout,
      });

      onUpdate();
    }
  }, [alertReceveChannelId, heartbeat, heartbeatStore, onUpdate, timeout]);

  const handleTimeoutChange = useCallback((value: SelectableValue) => {
    setTimeoutSeconds(value.value);
  }, []);

  const heartbeatStatus = Boolean(heartbeat?.status);

  const timeoutOptions = heartbeatStore.timeoutOptions;

  return (
    <div className={cx('root')}>
      <HorizontalGroup>
        {heartbeatStatus ? <HeartGreenIcon /> : <HeartRedIcon />}
        {heartbeat && (
          <Text>
            {heartbeat.last_heartbeat_time_verbal
              ? `Heartbeat received ${heartbeat.last_heartbeat_time_verbal} ago`
              : 'A heartbeat has not been received.'}
          </Text>
        )}
      </HorizontalGroup>
      <br />
      <br />
      <p>
        A heartbeat acts as a healthcheck for alert group monitoring. You can configure OnCall to regularly send alerts
        to the heartbeat endpoint. If you don't receive one of these alerts, OnCall will issue an alert group.
      </p>
      <p>
        <span>OnCall will issue an alert group if no alert is received every</span>
        <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
          <Select
            className={cx('select', 'timeout')}
            onChange={handleTimeoutChange}
            placeholder="Heartbeat Timeout"
            value={timeout}
            options={(timeoutOptions || []).map((timeoutOption: SelectOption) => ({
              value: timeoutOption.value,
              label: timeoutOption.display_name,
            }))}
          />
        </WithPermissionControlTooltip>
      </p>
      {heartbeat && (
        <p>
          <Text>Use the following unique Grafana link to send GET and POST requests:</Text>
          <pre>
            <code>{heartbeat?.link}</code>
          </pre>
        </p>
      )}
      {heartbeat && (
        <p>
          To send periodic heartbeat alerts from <Emoji text={alertReceiveChannel?.verbal_name || ''} /> to OnCall, do
          the following:
          <span
            dangerouslySetInnerHTML={{
              __html: heartbeat?.instruction,
            }}
          />
        </p>
      )}
      <HorizontalGroup className={cx('buttons')}>
        <WithPermissionControlTooltip key="ok" userAction={UserActions.IntegrationsWrite}>
          <Button variant="primary" onClick={handleOkClick}>
            {heartbeat ? 'Save' : 'Create'}
          </Button>
        </WithPermissionControlTooltip>
      </HorizontalGroup>
    </div>
  );
});

export default withMobXProviderContext(HeartbeatForm);
