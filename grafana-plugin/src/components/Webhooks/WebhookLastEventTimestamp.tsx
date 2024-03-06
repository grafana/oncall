import React from 'react';

import { css } from '@emotion/css';
import { useTheme2, useStyles2, HorizontalGroup, Button } from '@grafana/ui';
import dayjs from 'dayjs';

import { Tag } from 'components/Tag/Tag';
import { getTzOffsetString } from 'models/timezone/timezone.helpers';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { OutgoingTabDrawerKey } from 'pages/integration/OutgoingTab/OutgoingTab.types';

import { WebhookStatusCodeBadge } from './WebhookStatusCodeBadge';

export const WebhookLastEventTimestamp = ({
  webhook,
  openDrawer,
}: {
  webhook: ApiSchemas['Webhook'];
  openDrawer: (key: OutgoingTabDrawerKey) => void;
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
      <WebhookStatusCodeBadge webhook={webhook} />
      <Button
        size="sm"
        icon="eye"
        tooltip="Go to event details"
        variant="secondary"
        className={styles.eventDetailsIconButton}
        onClick={() => openDrawer('webhookDetails')}
      />
    </HorizontalGroup>
  );
};

export const getStyles = () => ({
  eventDetailsIconButton: css({
    padding: '6px 10px',
  }),
});
