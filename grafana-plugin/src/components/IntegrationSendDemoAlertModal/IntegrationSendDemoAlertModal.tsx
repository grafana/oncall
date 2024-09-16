import React, { useState } from 'react';

import { Button, Icon, Modal, Tooltip, Stack, useStyles2 } from '@grafana/ui';
import { StackSize } from 'helpers/consts';
import { openNotification } from 'helpers/helpers';
import CopyToClipboard from 'react-copy-to-clipboard';
import Emoji from 'react-emoji-render';
import { debounce } from 'throttle-debounce';

import { MonacoEditor, MonacoLanguage } from 'components/MonacoEditor/MonacoEditor';
import { MONACO_EDITABLE_CONFIG } from 'components/MonacoEditor/MonacoEditor.config';
import { PluginLink } from 'components/PluginLink/PluginLink';
import { Text } from 'components/Text/Text';
import { AlertReceiveChannelHelper } from 'models/alert_receive_channel/alert_receive_channel.helpers';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { getIntegrationStyles } from 'pages/integration/Integration.styles';
import { useStore } from 'state/useStore';

interface IntegrationSendDemoPayloadModalProps {
  isOpen: boolean;
  alertReceiveChannel: ApiSchemas['AlertReceiveChannel'];
  onHideOrCancel: () => void;
}

export const IntegrationSendDemoAlertModal: React.FC<IntegrationSendDemoPayloadModalProps> = ({
  alertReceiveChannel,
  isOpen,
  onHideOrCancel,
}) => {
  const store = useStore();
  const styles = useStyles2(getIntegrationStyles);
  const { alertReceiveChannelStore } = store;
  const initialDemoJSON = JSON.stringify(alertReceiveChannel.demo_alert_payload, null, 2);
  const [demoPayload, setDemoPayload] = useState<string>(initialDemoJSON);
  let onPayloadChangeDebounced = debounce(100, onPayloadChange);

  return (
    <Modal
      closeOnBackdropClick={false}
      closeOnEscape
      isOpen={isOpen}
      onDismiss={onHideOrCancel}
      title={
        <Stack>
          <Text.Title level={4}>
            Send demo alert to integration: {''}
            <strong>
              <Emoji text={alertReceiveChannel.verbal_name} />
            </strong>
          </Text.Title>
        </Stack>
      }
    >
      <Stack direction="column">
        <Stack gap={StackSize.xs}>
          <Text type={'secondary'}>Alert Payload</Text>
          <Tooltip
            content={
              <>
                Modify the provided payload to test integration routes, templates, and escalations. Enable Debug
                maintenance on the integration to prevent real notifications.
              </>
            }
            placement={'top-start'}
          >
            <Icon name={'info-circle'} />
          </Tooltip>
        </Stack>

        <div className={styles.integrationPayloadInput}>
          <MonacoEditor
            value={initialDemoJSON}
            disabled={true}
            height={`60vh`}
            useAutoCompleteList={false}
            language={MonacoLanguage.json}
            data={undefined}
            monacoOptions={MONACO_EDITABLE_CONFIG}
            showLineNumbers={false}
            onChange={onPayloadChangeDebounced}
          />
        </div>

        <Stack justifyContent={'flex-end'} gap={StackSize.md}>
          <Button variant={'secondary'} onClick={onHideOrCancel}>
            Cancel
          </Button>
          <CopyToClipboard text={getCurlText()} onCopy={() => openNotification('CURL has been copied')}>
            <Button variant={'secondary'}>Copy as CURL</Button>
          </CopyToClipboard>
          <Button variant={'primary'} onClick={onSendAlert} data-testid="submit-send-alert">
            Send Alert
          </Button>
        </Stack>
      </Stack>
    </Modal>
  );

  function onPayloadChange(value: string) {
    setDemoPayload(value);
  }

  async function onSendAlert() {
    let parsedPayload = undefined;
    try {
      parsedPayload = JSON.parse(demoPayload);
    } catch (ex) {}

    await AlertReceiveChannelHelper.sendDemoAlert(alertReceiveChannel.id, parsedPayload);
    alertReceiveChannelStore.fetchCounters();
    openNotification(<DemoNotification />);
    onHideOrCancel();
  }

  function getCurlText() {
    return `curl -X POST \
      ${alertReceiveChannel?.integration_url} \
      -H 'Content-Type: Application/json' \
      -d '${demoPayload}'`;
  }
};

const DemoNotification: React.FC = () => {
  return (
    <div data-testid="demo-alert-sent-notification">
      Demo alert was generated. Find it on the
      <PluginLink query={{ page: 'alert-groups' }}> "Alert Groups" </PluginLink>
      page and make sure it didn't freak out your colleagues 😉
    </div>
  );
};
