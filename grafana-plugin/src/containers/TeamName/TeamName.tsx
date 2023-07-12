import React from 'react';

import { Badge, Tooltip } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import Avatar from 'components/Avatar/Avatar';
import Text from 'components/Text/Text';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';

import styles from './TeamName.module.css';

const cx = cn.bind(styles);

interface TeamNameProps {
  team: GrafanaTeam;
  size?: 'small' | 'medium' | 'large';
}

const TeamName = observer((props: TeamNameProps) => {
  const { team, size = 'medium' } = props;
  if (!team) {
    return null;
  }
  if (team.id === 'null') {
    return <Badge text={team.name} color={'blue'} tooltip={'Resource is not assigned to any team (ex General team)'} />;
  }
  return (
    <Text type="secondary" size={size}>
      <Avatar size="small" src={team.avatar_url} className={cx('avatar')} />
      <Tooltip placement="top" content={'Resource is assigned to ' + team.name}>
        <Text type="primary">{team.name}</Text>
      </Tooltip>
    </Text>
  );
});

export default TeamName;
