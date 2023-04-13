import React from 'react';

import { Drawer, Label, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import Block from 'components/GBlock/Block';
import SourceCode from 'components/SourceCode/SourceCode';
import Text from 'components/Text/Text';
import { OutgoingWebhook2 } from 'models/outgoing_webhook_2/outgoing_webhook_2.types';
import { useStore } from 'state/useStore';

import styles from 'containers/OutgoingWebhook2Form/OutgoingWebhook2Form.module.css';

const cx = cn.bind(styles);

interface OutgoingWebhook2StatusProps {
  id: OutgoingWebhook2['id'];
  onHide: () => void;
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

const OutgoingWebhook2Status = observer((props: OutgoingWebhook2StatusProps) => {
  const { id, onHide } = props;

  const store = useStore();

  const { outgoingWebhook2Store } = store;

  const data = outgoingWebhook2Store.items[id];

  return (
    <Drawer
      scrollableContent
      title={
        <Text.Title className={cx('title')} level={4}>
          Outgoing Webhook Status
        </Text.Title>
      }
      onClose={onHide}
      closeOnMaskClick
    >
      <div className={cx('content')}>
        <VerticalGroup>
          <Label>Webhook Name</Label>
          <SourceCode showClipboardIconOnly>{data.name}</SourceCode>
          <Label>Trigger Type</Label>
          <SourceCode showClipboardIconOnly>{data.trigger_type_name}</SourceCode>

          {data.last_response_log.timestamp ? (
            <VerticalGroup>
              <Label>Last Run Time</Label>
              <SourceCode showClipboardIconOnly>{data.last_response_log.timestamp}</SourceCode>

              {data.last_response_log.request_trigger && (
                <Debug
                  title="Trigger Template"
                  source={data.trigger_template}
                  result={data.last_response_log.request_trigger}
                ></Debug>
              )}
              {data.last_response_log.url && (
                <Debug title="URL" source={data.url} result={data.last_response_log.url}></Debug>
              )}
              {data.last_response_log.request_headers && (
                <Debug title="Headers" source={data.headers} result={data.last_response_log.request_headers}></Debug>
              )}
              {data.last_response_log.request_data && (
                <Debug title="Data" source={data.data} result={data.last_response_log.request_data}></Debug>
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
                  <SourceCode showClipboardIconOnly>
                    {JSON.stringify(data.last_response_log.content, null, 4)}
                  </SourceCode>
                </VerticalGroup>
              )}
            </VerticalGroup>
          ) : (
            <Text type="primary" size="medium">
              An event triggering this webhook has not been sent yet!
            </Text>
          )}
        </VerticalGroup>
      </div>
    </Drawer>
  );
});

export default OutgoingWebhook2Status;
