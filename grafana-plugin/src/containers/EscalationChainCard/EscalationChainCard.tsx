import React from 'react';

import { Stack, Badge } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import { Text } from 'components/Text/Text';
import { TeamName } from 'containers/TeamName/TeamName';
import { EscalationChain } from 'models/escalation_chain/escalation_chain.types';
import { useStore } from 'state/useStore';
import { StackSize } from 'utils/consts';

import styles from './EscalationChainCard.module.css';

const cx = cn.bind(styles);

interface AlertReceiveChannelCardProps {
  id: EscalationChain['id'];
}

export const EscalationChainCard = observer((props: AlertReceiveChannelCardProps) => {
  const { id } = props;

  const store = useStore();

  const { escalationChainStore, grafanaTeamStore } = store;

  const escalationChain = escalationChainStore.items[id];

  return (
    <div className={cx('root')}>
      <Stack alignItems="flex-start">
        <Stack direction="column" gap={StackSize.xs}>
          <Stack gap={StackSize.sm}>
            <Text type="primary" size="medium">
              {escalationChain.name}
            </Text>
            <Badge
              text={escalationChain.number_of_integrations}
              color="green"
              icon="link"
              tooltip={
                escalationChain.number_of_integrations > 0 || escalationChain.number_of_routes > 0
                  ? `Modifying this escalation chain will affect ${escalationChain.number_of_integrations} integrations and ${escalationChain.number_of_routes} routes.`
                  : 'This escalation is not connected to any integration route, go to integrations and connect route to this escalation chain'
              }
            />
          </Stack>
          <TeamName team={grafanaTeamStore.items[escalationChain.team]} size="small" />
        </Stack>
      </Stack>
    </div>
  );
});
