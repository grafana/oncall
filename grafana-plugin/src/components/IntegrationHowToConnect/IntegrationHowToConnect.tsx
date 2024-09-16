import React from 'react';

import { Icon, Stack, useStyles2 } from '@grafana/ui';
import { StackSize } from 'helpers/consts';
import { noop } from 'lodash-es';
import { getUtilStyles } from 'styles/utils.styles';

import { IntegrationInputField } from 'components/IntegrationInputField/IntegrationInputField';
import { IntegrationBlock } from 'components/Integrations/IntegrationBlock';
import { IntegrationTag } from 'components/Integrations/IntegrationTag';
import { Text } from 'components/Text/Text';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { getIntegrationStyles } from 'pages/integration/Integration.styles';
import { useStore } from 'state/useStore';

export const IntegrationHowToConnect: React.FC<{ id: ApiSchemas['AlertReceiveChannel']['id'] }> = ({ id }) => {
  const { alertReceiveChannelStore } = useStore();
  const alertReceiveChannelCounter = alertReceiveChannelStore.counters[id];
  const hasAlerts = !!alertReceiveChannelCounter?.alerts_count;
  const styles = useStyles2(getIntegrationStyles);
  const utilStyles = useStyles2(getUtilStyles);

  const item = alertReceiveChannelStore.items[id];
  const url = item?.integration_url || item?.inbound_email;

  const howToConnectTagName = (integration: string) => {
    switch (integration) {
      case 'direct_paging':
        return 'Manual';
      case 'inbound_email':
        return 'Inbound Email';
      default:
        return 'HTTP Endpoint';
    }
  };

  return (
    <IntegrationBlock
      noContent={hasAlerts}
      toggle={noop}
      heading={
        <div className={styles.howToConnectContainer}>
          <IntegrationTag>{howToConnectTagName(item?.integration)}</IntegrationTag>
          {item?.integration === 'direct_paging' ? (
            <>
              <Text type="secondary">Alert Groups raised manually via Web or ChatOps</Text>
              <a
                href="https://grafana.com/docs/oncall/latest/integrations/manual"
                target="_blank"
                rel="noreferrer"
                className={utilStyles.pullRight}
              >
                <Text type="link" size="small">
                  <Stack>
                    How it works
                    <Icon name="external-link-alt" />
                  </Stack>
                </Text>
              </a>
            </>
          ) : (
            <>
              {url && (
                <IntegrationInputField
                  value={url}
                  isMasked
                  className={styles.integrationInputField}
                  showExternal={!!item?.integration_url}
                />
              )}
              <a
                href="https://grafana.com/docs/oncall/latest/integrations/"
                target="_blank"
                rel="noreferrer"
                className={utilStyles.pullRight}
              >
                <Text type="link" size="small">
                  <Stack>
                    How to connect
                    <Icon name="external-link-alt" />
                  </Stack>
                </Text>
              </a>
            </>
          )}
        </div>
      }
      content={hasAlerts ? null : renderContent()}
    />
  );

  function renderContent() {
    const callToAction = () => {
      if (item?.integration === 'direct_paging') {
        return <Text type={'primary'}>try to raise a demo alert group via Web or Chatops</Text>;
      } else {
        return item.demo_alert_enabled && <Text type={'primary'}>try to send a demo alert</Text>;
      }
    };

    return (
      <Stack direction="column" justifyContent={'flex-start'} gap={StackSize.xs}>
        {!hasAlerts && (
          <Stack gap={StackSize.xs}>
            <Icon name="fa fa-spinner" size="md" className={utilStyles.loadingPlaceholder} />
            <Text type={'primary'}>No alerts yet</Text> {callToAction()}
          </Stack>
        )}
      </Stack>
    );
  }
};
