import React from 'react';

import { HorizontalGroup, VerticalGroup } from '@grafana/ui';
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
          <Text type="primary" size="medium">
            {escalationChain.name}
          </Text>
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
