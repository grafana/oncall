import React, { useEffect, useState } from 'react';
import { observer } from 'mobx-react';

import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { withMobXProviderContext } from 'state/withStore';

import cn from 'classnames/bind';

import { Button, Drawer, Field, HorizontalGroup, Select, VerticalGroup } from '@grafana/ui';
import Text from 'components/Text/Text';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { UserActions } from 'utils/authorization';
import { useStore } from 'state/useStore';
import { SelectOption } from 'state/types';
import { SelectableValue } from '@grafana/data';

import IntegrationInputField from 'components/IntegrationInputField/IntegrationInputField';

const cx = cn.bind({});

interface Integration2HearbeatFormProps {
  alertReceveChannelId: AlertReceiveChannel['id'];
  onClose?: () => void;
}

const Integration2HearbeatForm = observer(({ alertReceveChannelId, onClose }: Integration2HearbeatFormProps) => {
  const [interval, setInterval] = useState<number>(undefined);

  const { heartbeatStore, alertReceiveChannelStore } = useStore();

  const alertReceiveChannel = alertReceiveChannelStore.items[alertReceveChannelId];

  const heartbeatId = alertReceiveChannelStore.alertReceiveChannelToHeartbeat[alertReceveChannelId];

  const heartbeat = heartbeatStore.items[heartbeatId];

  useEffect(() => {
    if (heartbeat) {
      setInterval(heartbeat.timeout_seconds);
    }
  }, [heartbeat]);

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
                {heartbeat ? 'Save' : 'Create'}
              </Button>
            </WithPermissionControlTooltip>
          </HorizontalGroup>
        </VerticalGroup>
      </VerticalGroup>
    </Drawer>
  );

  async function onSave() {
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
  }
});

export default withMobXProviderContext(Integration2HearbeatForm) as ({
  alertReceveChannelId,
}: Integration2HearbeatFormProps) => JSX.Element;
