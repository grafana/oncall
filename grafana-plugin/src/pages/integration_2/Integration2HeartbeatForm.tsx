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

interface Integration2HearbeatFormProps {
  alertReceveChannelId: AlertReceiveChannel['id'];
  onClose?: () => void;
}

const Integration2HearbeatForm = observer(({ alertReceveChannelId, onClose }: Integration2HearbeatFormProps) => {
  const [interval, setInterval] = useState<number>(undefined);

  const { heartbeatStore, alertReceiveChannelStore } = useStore();

  const alertReceiveChannel = alertReceiveChannelStore.items[alertReceveChannelId];

  useEffect(() => {
    heartbeatStore.updateTimeoutOptions();
  }, [heartbeatStore]);

  useEffect(() => {
    if (alertReceiveChannel.heartbeat) {
      setInterval(alertReceiveChannel.heartbeat.timeout_seconds);
    }
  }, [alertReceiveChannel]);

  const timeoutOptions = heartbeatStore.timeoutOptions;

  return (
    <Drawer width={'600px'} scrollableContent title={'Heartbeat'} onClose={onClose} closeOnMaskClick={false}>
      <VerticalGroup spacing={'lg'}>
        <Text type="secondary">
          Start maintenance mode when performing scheduled maintenance or updates on the infrastructure, which may
          trigger false alarms.
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
              <IntegrationInputField value={alertReceiveChannel?.integration_url} showEye={false} isMasked={false} />
            </Field>
          </div>
        </VerticalGroup>

        <VerticalGroup style={{ marginTop: 'auto' }}>
          <HorizontalGroup className={cx('buttons')} justify="flex-end">
            <Button variant={'secondary'} onClick={onClose}>
              Cancel
            </Button>
            <WithPermissionControlTooltip key="ok" userAction={UserActions.IntegrationsWrite}>
              <Button variant="primary" onClick={onSave}>
                {alertReceiveChannel.heartbeat ? 'Save' : 'Create'}
              </Button>
            </WithPermissionControlTooltip>
          </HorizontalGroup>
        </VerticalGroup>
      </VerticalGroup>
    </Drawer>
  );

  async function onSave() {
    const heartbeat = alertReceiveChannel.heartbeat;

    if (heartbeat) {
      await heartbeatStore.saveHeartbeat(heartbeat.id, {
        alert_receive_channel: heartbeat.alert_receive_channel,
        timeout_seconds: interval,
      });

      onClose();
    } else {
      await heartbeatStore.createHeartbeat(alertReceveChannelId, {
        timeout_seconds: interval,
      });

      onClose();
    }

    await alertReceiveChannelStore.updateItem(alertReceveChannelId);
  }
});

export default withMobXProviderContext(Integration2HearbeatForm) as ({
  alertReceveChannelId,
}: Integration2HearbeatFormProps) => JSX.Element;
