import React, { FC, useMemo } from 'react';

import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { VerticalGroup, HorizontalGroup, Badge, useStyles2, useTheme2 } from '@grafana/ui';
import dayjs from 'dayjs';

import { SourceCode } from 'components/SourceCode/SourceCode';
import { Tabs } from 'components/Tabs/Tabs';
import { Text } from 'components/Text/Text';
import { getTzOffsetString } from 'models/timezone/timezone.helpers';
import { ApiSchemas } from 'network/oncall-api/api.types';

import { WebhookStatusCodeBadge } from './WebhookStatusCodeBadge';

interface WebhookLastEventDetailsProps {
  webhook: ApiSchemas['Webhook'];
  sourceCodeRootClassName?: string;
}

export const WebhookLastEventDetails: FC<WebhookLastEventDetailsProps> = ({ webhook, sourceCodeRootClassName }) => {
  const styles = useStyles2(getStyles);
  const theme = useTheme2();
  const rows = useMemo(() => getEventDetailsRows(theme, webhook), [theme, webhook]);

  const commonSourceCodeProps = {
    showClipboardIconOnly: true,
    prettifyJsonString: true,
    noMaxHeight: true,
    rootClassName: sourceCodeRootClassName,
    preClassName: styles.sourceCodePre,
  };

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
        <VerticalGroup spacing="md">
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
              <SourceCode {...commonSourceCodeProps}>{webhook.last_response_log.request_data || 'No data'}</SourceCode>
            ),
          },
          {
            label: 'Response body',
            content: (
              <SourceCode {...commonSourceCodeProps}>{webhook.last_response_log.content || 'No data'}</SourceCode>
            ),
          },
          {
            label: 'Request headers',
            content: (
              <SourceCode {...commonSourceCodeProps}>
                {webhook.last_response_log.request_headers || 'No data'}
              </SourceCode>
            ),
          },
        ]}
      />
    </>
  );
};

const getEventDetailsRows = (theme: GrafanaTheme2, webhook?: ApiSchemas['Webhook']) =>
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
          value: <span>{webhook.last_response_log?.url || 'No data'}</span>,
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
  sourceCodePre: css({
    height: '100%',
  }),
});
