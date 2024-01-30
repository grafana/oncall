import React, { FC, useMemo } from 'react';

import { css } from '@emotion/css';
import { VerticalGroup, HorizontalGroup, Badge, useStyles2 } from '@grafana/ui';
import dayjs from 'dayjs';

import SourceCode from 'components/SourceCode/SourceCode';
import Tabs from 'components/Tabs/Tabs';
import Text from 'components/Text/Text';
import { OutgoingWebhook } from 'models/outgoing_webhook/outgoing_webhook.types';
import { getTzOffsetString } from 'models/timezone/timezone.helpers';

import WebhookStatusCodeBadge from './WebhookStatusCodeBadge';

interface WebhookLastEventDetailsProps {
  webhook: OutgoingWebhook;
}

const WebhookLastEventDetails: FC<WebhookLastEventDetailsProps> = ({ webhook }) => {
  const styles = useStyles2(getStyles);
  const rows = useMemo(() => getEventDetailsRows(webhook), [webhook]);

  if (!webhook.last_response_log?.timestamp) {
    return (
      <Text type="primary" size="medium">
        An event triggering of this webhook has not been sent yet.
      </Text>
    );
  }
  return (
    <>
      <div className={styles.lastEventDetailsRowsWrapper}>
        <VerticalGroup spacing="lg">
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
          {
            label: 'Event body',
            content: (
              <SourceCode showClipboardIconOnly prettifyJsonString noMaxHeight className={styles.sourceCode}>
                {webhook.last_response_log.request_data || 'No data'}
              </SourceCode>
            ),
          },
          {
            label: 'Response body',
            content: (
              <SourceCode showClipboardIconOnly prettifyJsonString noMaxHeight className={styles.sourceCode}>
                {webhook.last_response_log.content || 'No data'}
              </SourceCode>
            ),
          },
          {
            label: 'Request headers',
            content: (
              <SourceCode showClipboardIconOnly prettifyJsonString noMaxHeight className={styles.sourceCode}>
                {webhook.last_response_log.request_headers || 'No data'}
              </SourceCode>
            ),
          },
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
          value: (
            <>
              {webhook.url}{' '}
              {webhook.last_response_log?.url && webhook.url !== webhook.last_response_log?.url && (
                <Badge color="red" text={webhook.last_response_log?.url} />
              )}
            </>
          ),
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
  sourceCode: css({
    height: 'calc(100vh - 585px)',
  }),
});

export default WebhookLastEventDetails;
