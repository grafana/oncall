import React from 'react';

import { Badge, Tooltip } from '@grafana/ui';
import { observer } from 'mobx-react';

import Avatar from 'components/Avatar/Avatar';
import Text from 'components/Text/Text';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';

interface TeamNameProps {
  team: GrafanaTeam;
}

const TeamName = observer((props: TeamNameProps) => {
  const { team } = props;
  return (
    <>
      {team.id === 'null' ? (
        <Badge text={team.name} color={'blue'} tooltip={'Resource is not assigned to any team (ex General team)'} />
      ) : (
        <Text type="secondary">
          <Avatar size="small" src={team.avatar_url} />{' '}
          <Tooltip placement="top" content={'Resource is assigned to ' + team.name}>
            <span>{team.name}</span>
          </Tooltip>{' '}
        </Text>
      )}
    </>
  );
});

export default TeamName;
