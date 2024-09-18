import React, { ReactElement, useEffect, useState } from 'react';

import { css, cx } from '@emotion/css';
import { SelectableValue } from '@grafana/data';
import { Button, Drawer, Field, Icon, Select, Stack } from '@grafana/ui';
import { UserActions } from 'helpers/authorization/authorization';
import { StackSize } from 'helpers/consts';
import { openNotification } from 'helpers/helpers';
import { observer } from 'mobx-react';

import { IntegrationInputField } from 'components/IntegrationInputField/IntegrationInputField';
import { Text } from 'components/Text/Text';
import { WithConfirm } from 'components/WithConfirm/WithConfirm';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { SelectOption } from 'state/types';
import { useStore } from 'state/useStore';
import { withMobXProviderContext } from 'state/withStore';

interface IntegrationHeartbeatFormProps {
  alertReceveChannelId: ApiSchemas['AlertReceiveChannel']['id'];
  onClose?: () => void;
}

const _IntegrationHeartbeatForm = observer(({ alertReceveChannelId, onClose }: IntegrationHeartbeatFormProps) => {
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
        <Stack direction="column" gap={StackSize.lg}>
          <Text type="secondary">
            A heartbeat acts as a healthcheck for alert group monitoring. You can configure you monitoring to regularly
            send alerts to the heartbeat endpoint. If OnCall doesn't receive one of these alerts, it will create an new
            alert group and escalate it
          </Text>

          <Stack direction="column" gap={StackSize.md}>
            <div
              className={css`
                width: 100%;
              `}
            >
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
            <div
              className={css`
                width: 100%;
              `}
            >
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
                <Stack>
                  How to configure heartbeats
                  <Icon name="external-link-alt" />
                </Stack>
              </Text>
            </a>
          </Stack>

          {/* TODO: Check if the styles were appended previously */}
          <Stack direction="column">
            <Stack justifyContent="flex-end">
              <Button variant={'secondary'} onClick={onClose} data-testid="close-heartbeat-form">
                Close
              </Button>
              <WithPermissionControlTooltip key="ok" userAction={UserActions.IntegrationsWrite}>
                <Button variant="primary" onClick={onSave} data-testid="update-heartbeat">
                  Update
                </Button>
              </WithPermissionControlTooltip>
              <WithPermissionControlTooltip key="reset" userAction={UserActions.IntegrationsWrite}>
                <WithConfirm title="Are you sure to reset integration heartbeat?" confirmText="Reset">
                  <Button variant="destructive" onClick={onReset} data-testid="reset-heartbeat">
                    Reset
                  </Button>
                </WithConfirm>
              </WithPermissionControlTooltip>
            </Stack>
          </Stack>
        </Stack>
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

    await alertReceiveChannelStore.fetchItemById(alertReceveChannelId);
  }

  async function onReset() {
    await heartbeatStore.resetHeartbeatAndRefetchIntegration(heartbeatId, alertReceveChannelId);
    onClose();
  }
});

export const IntegrationHeartbeatForm = withMobXProviderContext(_IntegrationHeartbeatForm) as ({
  alertReceveChannelId,
}: IntegrationHeartbeatFormProps) => ReactElement;
