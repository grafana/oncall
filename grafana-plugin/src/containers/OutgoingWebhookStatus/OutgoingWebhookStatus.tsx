import React from 'react';

import { Label, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import Block from 'components/GBlock/Block';
import SourceCode from 'components/SourceCode/SourceCode';
import Text from 'components/Text/Text';
import { OutgoingWebhook } from 'models/outgoing_webhook/outgoing_webhook.types';
import { useStore } from 'state/useStore';

import styles from 'containers/OutgoingWebhookForm/OutgoingWebhookForm.module.css';

const cx = cn.bind(styles);

interface OutgoingWebhookStatusProps {
  id: OutgoingWebhook['id'];
  onUpdate: () => void;
}

function Debug(props) {
  return (
    <VerticalGroup spacing="none">
      <Label>{props.title}</Label>
      <Block bordered fullWidth>
        <VerticalGroup spacing="none">
          {props.source && <SourceCode showClipboardIconOnly>{props.source}</SourceCode>}
          {props.result && props.result !== props.source && (
            <VerticalGroup spacing="none">
              <Label>Result</Label>
              <SourceCode showClipboardIconOnly>{props.result}</SourceCode>
            </VerticalGroup>
          )}
        </VerticalGroup>
      </Block>
    </VerticalGroup>
  );
}

function format_response_field(str) {
  try {
    const jsonValue = JSON.parse(str);
    return JSON.stringify(jsonValue, null, 4);
  } catch (e) {
    return str;
  }
}

const OutgoingWebhookStatus = observer((props: OutgoingWebhookStatusProps) => {
  const { id } = props;

  const store = useStore();

  const { outgoingWebhookStore } = store;

  const data = outgoingWebhookStore.items[id];

  return (
    <div className={cx('content')}>
      <VerticalGroup>
        <Label>Webhook Name</Label>
        <SourceCode showClipboardIconOnly>{data.name}</SourceCode>
        <Label>Webhook ID</Label>
        <SourceCode showClipboardIconOnly>{data.id}</SourceCode>
        <Label>Trigger Type</Label>
        <SourceCode showClipboardIconOnly>{data.trigger_type_name}</SourceCode>

        {data.last_response_log.timestamp ? (
          <VerticalGroup>
            <Label>Last Run Time</Label>
            <SourceCode showClipboardIconOnly>{data.last_response_log.timestamp}</SourceCode>

            {data.last_response_log.url && (
              <Debug title="URL" source={data.url} result={data.last_response_log.url}></Debug>
            )}
            {data.last_response_log.status_code && (
              <VerticalGroup>
                <Label>Response Code</Label>
                <SourceCode showClipboardIconOnly>{data.last_response_log.status_code}</SourceCode>
              </VerticalGroup>
            )}

            {data.last_response_log.content && (
              <VerticalGroup>
                <Label>Response Body</Label>
                <SourceCode showClipboardIconOnly>{format_response_field(data.last_response_log.content)}</SourceCode>
              </VerticalGroup>
            )}
            {data.last_response_log.request_trigger && (
              <Debug
                title="Trigger Template"
                source={data.trigger_template}
                result={data.last_response_log.request_trigger}
              ></Debug>
            )}
            {data.last_response_log.request_headers && (
              <Debug
                title="Request Headers"
                source={data.headers}
                result={data.last_response_log.request_headers}
              ></Debug>
            )}
            {data.last_response_log.request_data && (
              <Debug
                title="Request Data"
                source={data.data}
                result={format_response_field(data.last_response_log.request_data)}
              ></Debug>
            )}
          </VerticalGroup>
        ) : (
          <Text type="primary" size="medium">
            An event triggering this webhook has not been sent yet!
          </Text>
        )}
      </VerticalGroup>
    </div>
  );
});

export default OutgoingWebhookStatus;
