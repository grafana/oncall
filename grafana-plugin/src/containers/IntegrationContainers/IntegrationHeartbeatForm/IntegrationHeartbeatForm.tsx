import React, { useEffect, useState } from 'react';

import { SelectableValue } from '@grafana/data';
import { Button, Drawer, Field, HorizontalGroup, Icon, Select, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import IntegrationInputField from 'components/IntegrationInputField/IntegrationInputField';
import Text from 'components/Text/Text';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { SelectOption } from 'state/types';
import { useStore } from 'state/useStore';
import { withMobXProviderContext } from 'state/withStore';
import { openNotification } from 'utils';
import { UserActions } from 'utils/authorization';

import styles from './IntegrationHeartbeatForm.module.scss';

const cx = cn.bind(styles);

interface IntegrationHeartbeatFormProps {
  alertReceveChannelId: AlertReceiveChannel['id'];
  onClose?: () => void;
}

const IntegrationHeartbeatForm = observer(({ alertReceveChannelId, onClose }: IntegrationHeartbeatFormProps) => {
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
      <div data-testid="heartbeat-settings-form">
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
                    isLoading={!timeoutOptions}
                    options={timeoutOptions?.map((timeoutOption: SelectOption) => ({
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
            <a
              href="https://grafana.com/docs/oncall/latest/integrations/alertmanager/#configuring-oncall-heartbeats-optional"
              target="_blank"
              rel="noreferrer"
            >
              <Text type="link" size="small">
                <HorizontalGroup>
                  How to configure heartbeats
                  <Icon name="external-link-alt" />
                </HorizontalGroup>
              </Text>
            </a>
          </VerticalGroup>

          <VerticalGroup style={{ marginTop: 'auto' }}>
            <HorizontalGroup className={cx('buttons')} justify="flex-end">
              <Button variant={'secondary'} onClick={onClose} data-testid="close-heartbeat-form">
                Close
              </Button>
              <WithPermissionControlTooltip key="ok" userAction={UserActions.IntegrationsWrite}>
                <Button variant="primary" onClick={onSave} data-testid="update-heartbeat">
                  Update
                </Button>
              </WithPermissionControlTooltip>
            </HorizontalGroup>
          </VerticalGroup>
        </VerticalGroup>
      </div>
    </Drawer>
  );

  async function onSave() {
    await heartbeatStore.saveHeartbeat(heartbeat.id, {
      alert_receive_channel: heartbeat.alert_receive_channel,
      timeout_seconds: interval,
    });

    onClose();

    openNotification('Heartbeat settings have been updated');

    await alertReceiveChannelStore.loadItem(alertReceveChannelId);
  }
});

export default withMobXProviderContext(IntegrationHeartbeatForm) as ({
  alertReceveChannelId,
}: IntegrationHeartbeatFormProps) => JSX.Element;
