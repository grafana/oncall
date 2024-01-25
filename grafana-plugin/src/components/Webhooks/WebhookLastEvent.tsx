import React from 'react';

import { css } from '@emotion/css';
import { useTheme2, useStyles2, HorizontalGroup, Badge, Button } from '@grafana/ui';
import dayjs from 'dayjs';

import Tag from 'components/Tag/Tag';
import { OutgoingWebhook } from 'models/outgoing_webhook/outgoing_webhook.types';
import { getTzOffsetString } from 'models/timezone/timezone.helpers';

export const WebhookLastEvent = ({
  webhook,
  openLastEvent,
}: {
  webhook: OutgoingWebhook;
  openLastEvent: () => void;
}) => {
  const theme = useTheme2();
  const styles = useStyles2(getStyles);

  const lastEventMoment = dayjs(webhook.last_response_log?.timestamp);

  const lastEventFormatted = `${lastEventMoment.format('DD MMM YYYY')}, ${lastEventMoment.format(
    'HH:mm:ss'
  )} (${getTzOffsetString(lastEventMoment)})`;

  const isLastEventDateValid = lastEventMoment.isValid();

  if (!isLastEventDateValid) {
    return (
      <Tag
        color={theme.colors.background.secondary}
        border={`1px solid ${theme.colors.border.weak}`}
        text={theme.colors.text.secondary}
        size="small"
      >
        Never
      </Tag>
    );
  }

  return (
    <HorizontalGroup>
      <Tag
        color={theme.colors.background.secondary}
        border={`1px solid ${theme.colors.border.weak}`}
        text={theme.colors.text.primary}
        size="small"
      >
        {lastEventFormatted}
      </Tag>
      <Badge
        color={webhook.last_response_log?.status_code?.startsWith?.('2') ? 'green' : 'orange'}
        text={webhook.last_response_log?.status_code || 'No status'}
        className={styles.lastEventBadge}
      />
      <Button
        size="sm"
        icon="eye"
        tooltip="Go to event details"
        variant="secondary"
        className={styles.eventDetailsIconButton}
        onClick={openLastEvent}
      />
    </HorizontalGroup>
  );
};

export const getStyles = () => ({
  eventDetailsIconButton: css({
    padding: '6px 10px',
  }),
  lastEventBadge: css({
    wordBreak: 'keep-all',
    whiteSpace: 'nowrap',
  }),
});
