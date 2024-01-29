import { VerticalGroup, HorizontalGroup, Badge, useStyles2 } from '@grafana/ui';
import dayjs from 'dayjs';
import { OutgoingWebhook } from 'models/outgoing_webhook/outgoing_webhook.types';
import { getTzOffsetString } from 'models/timezone/timezone.helpers';
import { getEventDetailsRows } from 'pages/integration/OutgoingTab/EventTriggerDetailsDrawerContent.utils';
import React, { FC, useMemo } from 'react';
import { css } from '@emotion/css';

import WebhookStatusCodeBadge from './WebhookStatusCodeBadge';
import Tabs from 'components/Tabs/Tabs';

interface WebhookLastEventDetailsProps {
  webhook: OutgoingWebhook;
}

const WebhookLastEventDetails: FC<WebhookLastEventDetailsProps> = ({ webhook }) => {
  const styles = useStyles2(getStyles);
  const rows = useMemo(() => getEventDetailsRows(webhook), [webhook]);

  return (
    <>
      <div className={styles.lastEventDetailsRowsWrapper}>
        {' '}
        <VerticalGroup>
          {rows.map(({ title, value }) => (
            <HorizontalGroup key={title}>
              <span className={styles.lastEventDetailsRowTitle}>{title}</span>
              <span className={styles.lastEventDetailsRowValue}>{value}</span>
            </HorizontalGroup>
          ))}
        </VerticalGroup>
      </div>
      <Tabs
        queryStringKey="lastEventDetailsActiveTab"
        tabs={[
          { label: 'Event content', content: <div>content</div> },
          { label: 'Request headers', content: <div>content</div> },
          { label: 'Response headers', content: <div>content</div> },
          { label: 'Response body', content: <div>content</div> },
        ]}
      />
    </>
  );
};

const getEventDetailsRows = (webhook?: OutgoingWebhook) =>
  webhook
    ? [
        {
          title: 'Trigger type',
          value: webhook.trigger_type_name,
        },
        {
          title: 'Time',
          value: `${dayjs(webhook.last_response_log?.timestamp).format('DD MMM YYYY, HH:mm')} (${getTzOffsetString(
            dayjs(webhook.last_response_log?.timestamp)
          )})`,
        },
        {
          title: 'URL',
          value: webhook.url,
        },
        {
          title: 'Method',
          value: <Badge color="blue" text={webhook.http_method} />,
        },
        {
          title: 'Response code',
          value: <WebhookStatusCodeBadge webhook={webhook} />,
        },
      ]
    : [];

const getStyles = () => ({
  lastEventDetailsRowTitle: css({
    width: '150px',
  }),
  lastEventDetailsRowValue: css({
    fontWeight: 500,
  }),
  lastEventDetailsRowsWrapper: css({
    marginBottom: '26px',
  }),
});

export default WebhookLastEventDetails;
