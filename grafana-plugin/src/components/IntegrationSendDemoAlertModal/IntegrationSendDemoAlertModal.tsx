import React, { useState } from 'react';

import { Button, HorizontalGroup, Icon, Modal, Tooltip, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import CopyToClipboard from 'react-copy-to-clipboard';
import Emoji from 'react-emoji-render';
import { debounce } from 'throttle-debounce';

import MonacoEditor, { MONACO_LANGUAGE } from 'components/MonacoEditor/MonacoEditor';
import { MONACO_EDITABLE_CONFIG } from 'components/MonacoEditor/MonacoEditor.config';
import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import styles from 'pages/integration/Integration.module.scss';
import { useStore } from 'state/useStore';
import { openNotification } from 'utils';

const cx = cn.bind(styles);

interface IntegrationSendDemoPayloadModalProps {
  isOpen: boolean;
  alertReceiveChannel: AlertReceiveChannel;
  onHideOrCancel: () => void;
}

const IntegrationSendDemoAlertModal: React.FC<IntegrationSendDemoPayloadModalProps> = ({
  alertReceiveChannel,
  isOpen,
  onHideOrCancel,
}) => {
  const store = useStore();
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
        <HorizontalGroup>
          <Text.Title level={4}>
            Send demo alert to integration: {''}
            <strong>
              <Emoji text={alertReceiveChannel.verbal_name} />
            </strong>
          </Text.Title>
        </HorizontalGroup>
      }
    >
      <VerticalGroup>
        <HorizontalGroup spacing={'xs'}>
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
        </HorizontalGroup>

        <div className={cx('integration__payloadInput')}>
          <MonacoEditor
            value={initialDemoJSON}
            disabled={true}
            height={`60vh`}
            useAutoCompleteList={false}
            language={MONACO_LANGUAGE.json}
            data={undefined}
            monacoOptions={MONACO_EDITABLE_CONFIG}
            showLineNumbers={false}
            onChange={onPayloadChangeDebounced}
          />
        </div>

        <HorizontalGroup justify={'flex-end'} spacing={'md'}>
          <Button variant={'secondary'} onClick={onHideOrCancel}>
            Cancel
          </Button>
          <CopyToClipboard text={getCurlText()} onCopy={() => openNotification('CURL has been copied')}>
            <Button variant={'secondary'}>Copy as CURL</Button>
          </CopyToClipboard>
          <Button variant={'primary'} onClick={sendDemoAlert} data-testid="submit-send-alert">
            Send Alert
          </Button>
        </HorizontalGroup>
      </VerticalGroup>
    </Modal>
  );

  function onPayloadChange(value: string) {
    setDemoPayload(value);
  }

  function sendDemoAlert() {
    let parsedPayload = undefined;
    try {
      parsedPayload = JSON.parse(demoPayload);
    } catch (ex) {}

    alertReceiveChannelStore.sendDemoAlert(alertReceiveChannel.id, parsedPayload).then(() => {
      alertReceiveChannelStore.updateCounters();
      openNotification(<DemoNotification />);
      onHideOrCancel();
    });
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

export default IntegrationSendDemoAlertModal;
