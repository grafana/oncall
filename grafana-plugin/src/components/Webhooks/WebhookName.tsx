import React from 'react';

import { css } from '@emotion/css';
import { Badge, Button, useStyles2 } from '@grafana/ui';

import { OutgoingWebhook } from 'models/outgoing_webhook/outgoing_webhook.types';

export const WebhookName = ({
  webhook: { is_webhook_enabled, name },
  onNameClick,
}: {
  webhook: OutgoingWebhook;
  onNameClick: () => void;
}) => {
  const styles = useStyles2(getStyles);

  return (
    <div className={styles.nameColumn}>
      <Button fill="text" className={styles.webhookName} onClick={onNameClick}>
        {name}
      </Button>
      {!is_webhook_enabled && <Badge className={styles.disabledBadge} text="Disabled" color="orange" icon="pause" />}
    </div>
  );
};

export const getStyles = () => ({
  nameColumn: css({
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
  }),
  webhookName: css({
    wordBreak: 'break-word',
    padding: 0,
    '&:hover': {
      background: 'none',
    },
  }),
  disabledBadge: css({
    wordBreak: 'keep-all',
  }),
});
