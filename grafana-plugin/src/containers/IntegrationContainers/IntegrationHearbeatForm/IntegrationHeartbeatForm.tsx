import React, { useEffect, useState } from 'react';

import { SelectableValue } from '@grafana/data';
import { Button, Drawer, Field, HorizontalGroup, Select, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import IntegrationInputField from 'components/IntegrationInputField/IntegrationInputField';
import Text from 'components/Text/Text';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { SelectOption } from 'state/types';
import { useStore } from 'state/useStore';
import { withMobXProviderContext } from 'state/withStore';
import { UserActions } from 'utils/authorization';

const cx = cn.bind({});

interface IntegrationHearbeatFormProps {
  alertReceveChannelId: AlertReceiveChannel['id'];
  onClose?: () => void;
}

const IntegrationHearbeatForm = observer(({ alertReceveChannelId, onClose }: IntegrationHearbeatFormProps) => {
  const [interval, setInterval] = useState<number>(undefined);

  const { heartbeatStore, alertReceiveChannelStore } = useStore();

  const alertReceiveChannel = alertReceiveChannelStore.items[alertReceveChannelId];
  const heartbeatId = alertReceiveChannelStore.alertReceiveChannelToHeartbeat[alertReceiveChannel.id];
  const heartbeat = heartbeatStore.items[heartbeatId];

  useEffect(() => {
    heartbeatStore.updateTimeoutOptions();
  }, []);

  useEffect(() => {
    setInterval(heartbeat.timeout_seconds);
  }, [heartbeat]);

  const timeoutOptions = heartbeatStore.timeoutOptions;

  return (
    <Drawer width={'640px'} scrollableContent title={'Heartbeat'} onClose={onClose} closeOnMaskClick={false}>
      <VerticalGroup spacing={'lg'}>
        <Text type="secondary">
          A heartbeat acts as a healthcheck for alert group monitoring. You can configure you monitoring to regularly
          send alerts to the heartbeat endpoint. If OnCall doen't receive one of these alerts, it will create an new
          alert group and escalate it
        </Text>

        <VerticalGroup spacing="md">
          <div className={cx('u-width-100')}>
            <Field label={'Setup heartbeat interval'}>
              <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
                <Select
                  className={cx('select', 'timeout')}
                  onChange={(value: SelectableValue) => setInterval(value.value)}
                  placeholder="Heartbeat Timeout"
                  value={interval}
                  options={(timeoutOptions || []).map((timeoutOption: SelectOption) => ({
                    value: timeoutOption.value,
                    label: timeoutOption.display_name,
                  }))}
                />
              </WithPermissionControlTooltip>
            </Field>
          </div>
          <div className={cx('u-width-100')}>
            <Field label="Endpoint" description="Use the following unique Grafana link to send GET and POST requests">
              <IntegrationInputField value={heartbeat?.link} showEye={false} isMasked={false} />
            </Field>
          </div>
          {/*  <p>
            To send periodic heartbeat alerts from <Emoji text={alertReceiveChannel?.verbal_name || ''} /> to OnCall, do
            the following:
            <span
              dangerouslySetInnerHTML={{
                __html: heartbeat.instruction,
              }}
            />
          </p> */}
        </VerticalGroup>

        <VerticalGroup style={{ marginTop: 'auto' }}>
          <HorizontalGroup className={cx('buttons')} justify="flex-end">
            <Button variant={'secondary'} onClick={onClose}>
              {heartbeat ? 'Close' : 'Cancel'}
            </Button>
            <WithPermissionControlTooltip key="ok" userAction={UserActions.IntegrationsWrite}>
              <Button variant="primary" onClick={onSave}>
                {heartbeat ? 'Save' : 'Create'}
              </Button>
            </WithPermissionControlTooltip>
          </HorizontalGroup>
        </VerticalGroup>
      </VerticalGroup>
    </Drawer>
  );

  async function onSave() {
    await heartbeatStore.saveHeartbeat(heartbeat.id, {
      alert_receive_channel: heartbeat.alert_receive_channel,
      timeout_seconds: interval,
    });

    onClose();

    await alertReceiveChannelStore.loadItem(alertReceveChannelId);
  }
});

export default withMobXProviderContext(IntegrationHearbeatForm) as ({
  alertReceveChannelId,
}: IntegrationHearbeatFormProps) => JSX.Element;
