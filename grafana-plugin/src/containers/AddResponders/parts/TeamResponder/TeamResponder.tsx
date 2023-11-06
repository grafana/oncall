import React, { FC } from 'react';

import { HorizontalGroup, IconButton } from '@grafana/ui';
import cn from 'classnames/bind';

import Avatar from 'components/Avatar/Avatar';
import Text from 'components/Text/Text';
import styles from 'containers/AddResponders/AddResponders.module.scss';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';

const cx = cn.bind(styles);

type Props = {
  team: GrafanaTeam | null;
  handleDelete: React.MouseEventHandler<HTMLButtonElement>;
};

const TeamResponder: FC<Props> = ({ team: { avatar_url, name }, handleDelete }) => (
  <li>
    <HorizontalGroup justify="space-between">
      <HorizontalGroup>
        <div className={cx('timeline-icon-background')}>
          <Avatar size="medium" src={avatar_url} />
        </div>
        <Text className={cx('responder-name')}>{name}</Text>
      </HorizontalGroup>
      <IconButton
        data-testid="team-responder-delete-icon"
        tooltip="Remove responder"
        name="trash-alt"
        onClick={handleDelete}
      />
    </HorizontalGroup>
  </li>
);

export default TeamResponder;
