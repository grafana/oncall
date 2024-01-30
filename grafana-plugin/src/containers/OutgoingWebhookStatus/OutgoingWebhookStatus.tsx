import React from 'react';

import { HorizontalGroup, Button } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import WebhookLastEventDetails from 'components/Webhooks/WebhookLastEventDetails';
import { OutgoingWebhook } from 'models/outgoing_webhook/outgoing_webhook.types';
import { useStore } from 'state/useStore';
import { useCommonStyles } from 'utils/hooks';

import styles from 'containers/OutgoingWebhookForm/OutgoingWebhookForm.module.css';

const cx = cn.bind(styles);

interface OutgoingWebhookStatusProps {
  id: OutgoingWebhook['id'];
  closeDrawer: () => void;
}

const OutgoingWebhookStatus = observer(({ id, closeDrawer }: OutgoingWebhookStatusProps) => {
  const {
    outgoingWebhookStore: {
      items: { [id]: webhook },
    },
  } = useStore();
  const commonStyles = useCommonStyles();

  return (
    <div className={cx('content')}>
      <WebhookLastEventDetails webhook={webhook} />
      <div className={commonStyles.bottomDrawerButtons}>
        <HorizontalGroup justify="flex-end">
          <Button variant="secondary" onClick={closeDrawer}>
            Close
          </Button>
        </HorizontalGroup>
      </div>
    </div>
  );
});

export default OutgoingWebhookStatus;
