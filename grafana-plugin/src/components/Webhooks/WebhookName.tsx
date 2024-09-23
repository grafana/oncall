import React from 'react';

import { css } from '@emotion/css';
import { Badge, Button, useStyles2 } from '@grafana/ui';

export const WebhookName = ({
  name,
  isEnabled,
  onNameClick,
  displayAsLink,
}: {
  name: string;
  isEnabled: boolean;
  onNameClick?: () => void;
  displayAsLink?: boolean;
}) => {
  const styles = useStyles2(getStyles);

  return (
    <div className={styles.nameColumn}>
      {displayAsLink ? (
        <Button fill="text" className={styles.webhookName} onClick={onNameClick}>
          {name}
        </Button>
      ) : (
        <span className={styles.webhookName}>{name}</span>
      )}

      {!isEnabled && <Badge className={styles.disabledBadge} text="Disabled" color="orange" icon="pause" />}
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
    marginLeft: '8px',
  }),
});
