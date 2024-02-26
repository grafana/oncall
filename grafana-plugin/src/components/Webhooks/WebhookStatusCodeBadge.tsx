import React, { FC } from 'react';

import { css } from '@emotion/css';
import { Badge, useStyles2 } from '@grafana/ui';

import { OutgoingWebhook } from 'models/outgoing_webhook/outgoing_webhook.types';

interface WebhookStatusCodeBadgeProps {
  webhook: OutgoingWebhook;
}

const WebhookStatusCodeBadge: FC<WebhookStatusCodeBadgeProps> = ({ webhook }) => {
  const styles = useStyles2(getStyles);

  return (
    <Badge
      color={webhook.last_response_log?.status_code?.startsWith?.('2') ? 'green' : 'orange'}
      text={webhook.last_response_log?.status_code || 'No status'}
      className={styles.lastEventBadge}
    />
  );
};

const getStyles = () => ({
  lastEventBadge: css({
    wordBreak: 'keep-all',
    whiteSpace: 'nowrap',
  }),
});

export default WebhookStatusCodeBadge;
