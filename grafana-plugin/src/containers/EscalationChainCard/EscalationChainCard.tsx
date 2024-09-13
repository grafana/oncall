import React from 'react';

import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { Stack, Badge, useStyles2 } from '@grafana/ui';
import { StackSize } from 'helpers/consts';
import { observer } from 'mobx-react';

import { Text } from 'components/Text/Text';
import { TeamName } from 'containers/TeamName/TeamName';
import { EscalationChain } from 'models/escalation_chain/escalation_chain.types';
import { useStore } from 'state/useStore';

interface AlertReceiveChannelCardProps {
  id: EscalationChain['id'];
}

export const EscalationChainCard = observer((props: AlertReceiveChannelCardProps) => {
  const { id } = props;

  const store = useStore();
  const styles = useStyles2(getStyles);

  const { escalationChainStore, grafanaTeamStore } = store;

  const escalationChain = escalationChainStore.items[id];

  return (
    <div className={styles.root}>
      <Stack alignItems="flex-start">
        <Stack direction="column" gap={StackSize.xs}>
          <Stack gap={StackSize.sm}>
            <Text type="primary" size="medium">
              {escalationChain.name}
            </Text>
            <div>
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
            </div>
          </Stack>

          <div>
            <TeamName team={grafanaTeamStore.items[escalationChain.team]} size="small" />
          </div>
        </Stack>
      </Stack>
    </div>
  );
});

const getStyles = (theme: GrafanaTheme2) => {
  return {
    root: css`
      display: block;
    `,
    icon: css`
      color: ${theme.colors.success.text};
    `,
  };
};
