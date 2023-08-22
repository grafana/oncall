import React from 'react';

import { HorizontalGroup, Icon, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { noop } from 'lodash-es';

import IntegrationInputField from 'components/IntegrationInputField/IntegrationInputField';
import IntegrationBlock from 'components/Integrations/IntegrationBlock';
import Tag from 'components/Tag/Tag';
import Text from 'components/Text/Text';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import styles from 'pages/integration/Integration.module.scss';
import { useStore } from 'state/useStore';
import { getVar } from 'utils/DOM';

const cx = cn.bind(styles);

const IntegrationHowToConnect: React.FC<{ id: AlertReceiveChannel['id'] }> = ({ id }) => {
  const { alertReceiveChannelStore } = useStore();
  const alertReceiveChannelCounter = alertReceiveChannelStore.counters[id];
  const hasAlerts = !!alertReceiveChannelCounter?.alerts_count;

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
        <div className={cx('how-to-connect__container')}>
          <Tag color={getVar('--tag-secondary-transparent')} border={getVar('--border-weak')} className={cx('tag')}>
            <Text type="primary" size="small" className={cx('radius')}>
              {howToConnectTagName(item?.integration)}
            </Text>
          </Tag>
          {item?.integration === 'direct_paging' ? (
            <>
              <Text type="secondary">Alert Groups raised manually via Web or ChatOps</Text>
              <a
                href="https://grafana.com/docs/oncall/latest/integrations/manual"
                target="_blank"
                rel="noreferrer"
                className={cx('u-pull-right')}
              >
                <Text type="link" size="small">
                  <HorizontalGroup>
                    How it works
                    <Icon name="external-link-alt" />
                  </HorizontalGroup>
                </Text>
              </a>
            </>
          ) : (
            <>
              {url && (
                <IntegrationInputField
                  value={url}
                  className={cx('integration__input-field')}
                  showExternal={!!item?.integration_url}
                />
              )}
              <a
                href="https://grafana.com/docs/oncall/latest/integrations/"
                target="_blank"
                rel="noreferrer"
                className={cx('u-pull-right')}
              >
                <Text type="link" size="small">
                  <HorizontalGroup>
                    How to connect
                    <Icon name="external-link-alt" />
                  </HorizontalGroup>
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
      <VerticalGroup justify={'flex-start'} spacing={'xs'}>
        {!hasAlerts && (
          <HorizontalGroup spacing={'xs'}>
            <Icon name="fa fa-spinner" size="md" className={cx('loadingPlaceholder')} />
            <Text type={'primary'}>No alerts yet;</Text> {callToAction()}
          </HorizontalGroup>
        )}
      </VerticalGroup>
    );
  }
};

export default IntegrationHowToConnect;
