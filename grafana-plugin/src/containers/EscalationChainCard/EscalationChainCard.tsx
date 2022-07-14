import React from 'react';

import { HorizontalGroup, Icon, VerticalGroup, Tooltip } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import Text from 'components/Text/Text';
import { EscalationChain } from 'models/escalation_chain/escalation_chain.types';
import { useStore } from 'state/useStore';

import styles from './EscalationChainCard.module.css';

const cx = cn.bind(styles);

interface AlertReceiveChannelCardProps {
  id: EscalationChain['id'];
}

const EscalationChainCard = observer((props: AlertReceiveChannelCardProps) => {
  const { id } = props;

  const store = useStore();

  const { escalationChainStore } = store;

  const escalationChain = escalationChainStore.items[id];

  return (
    <div className={cx('root')}>
      <HorizontalGroup align="flex-start">
        <VerticalGroup spacing="xs">
          <HorizontalGroup spacing="sm">
            <Text type="primary" size="medium">
              {escalationChain.name}
            </Text>
            {(escalationChain.number_of_integrations > 0 || escalationChain.number_of_routes > 0) && (
              <Tooltip
                placement="top"
                content={`Modifying this escalation chain will affect ${escalationChain.number_of_integrations} integrations and ${escalationChain.number_of_routes} routes.`}
              >
                <div className={cx('connected-integrations')}>
                  <HorizontalGroup spacing="xs">
                    <Icon className={cx('icon')} name="link" size="sm" />
                    <Text type="success" size="small">
                      {escalationChain.number_of_integrations}
                    </Text>
                  </HorizontalGroup>
                </div>
              </Tooltip>
            )}
          </HorizontalGroup>
          {/*<HorizontalGroup>
            <PluginLink
              query={{ page: 'incidents', integration: alertReceiveChannel.id }}
              className={cx('alertsInfoText')}
            >
              <b>{alertReceiveChannel.alert_count}</b> alerts in <b>{alertReceiveChannel.alert_groups_count}</b>{' '}
              incidents
            </PluginLink>
            <Text type="secondary" size="small">
              |
            </Text>
            <IntegrationLogo scale={0.08} integration={integration} />
            <Text type="secondary" size="small">
              {integration?.display_name}
            </Text>
          </HorizontalGroup>*/}
        </VerticalGroup>
      </HorizontalGroup>
    </div>
  );
});

export default EscalationChainCard;
