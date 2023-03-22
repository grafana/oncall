import React from 'react';

import { Badge, Tooltip } from '@grafana/ui';
import { observer } from 'mobx-react';

import Avatar from 'components/Avatar/Avatar';
import Text from 'components/Text/Text';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';

interface TeamNameProps {
  team: GrafanaTeam;
  size?: 'small' | 'medium' | 'large';
}

const TeamName = observer((props: TeamNameProps) => {
  const { team, size } = props;
  if (!team) {
    return '';
  }
  if (team.id === 'null') {
    return <Badge text={team.name} color={'blue'} tooltip={'Resource is not assigned to any team (ex General team)'} />;
  }
  return (
    <Text type="secondary" size={size ? size : 'medium'}>
      <Avatar size="small" src={team.avatar_url} />{' '}
      <Tooltip placement="top" content={'Resource is assigned to ' + team.name}>
        <span>{team.name}</span>
      </Tooltip>{' '}
    </Text>
  );
});

export default TeamName;
