import React from 'react';
import { observer } from 'mobx-react';

import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { withMobXProviderContext } from 'state/withStore';

import Integration2HeartbeatForm from './Integration2HeartbeatForm.config';
import { Drawer, VerticalGroup } from '@grafana/ui';
import GForm from 'components/GForm/GForm';
import Text from 'components/Text/Text';

interface Integration2HearbeatFormProps {
  alertReceveChannelId: AlertReceiveChannel['id'];
  onUpdate: () => void;
}

const Integration2HearbeatForm = observer(({ alertReceveChannelId }: Integration2HearbeatFormProps) => {
  const onHide = () => {};
  const data: { alert_receive_channel: AlertReceiveChannel['id'] } = { alert_receive_channel: alertReceveChannelId };

  const handleSubmit = () => {};

  return (
    <Drawer scrollableContent title={'Heartbeat'} onClose={onHide} closeOnMaskClick={false}>
      <div>
        <Text type="secondary">
          A heartbeat acts as a healthcheck for alert group monitoring. You can configure OnCall to regularly send
          alerts to the heartbeat endpoint. If you don't receive one of these alerts, OnCall will issue an alert group.
        </Text>

        <VerticalGroup>
          <GForm form={Integration2HeartbeatForm} data={data} onSubmit={handleSubmit} />
        </VerticalGroup>
      </div>
    </Drawer>
  );
});

export default withMobXProviderContext(Integration2HearbeatForm);
