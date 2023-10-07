import React, { FC } from 'react';

import { HorizontalGroup, IconButton } from '@grafana/ui';
import cn from 'classnames/bind';

import Avatar from 'components/Avatar/Avatar';
import Text from 'components/Text/Text';
import styles from 'containers/EscalationVariants/EscalationVariants.module.scss';
import {
  ResponderBaseProps,
  TeamResponder as TeamResponderType,
} from 'containers/EscalationVariants/EscalationVariants.types';
import NotificationPoliciesSelect from 'containers/EscalationVariants/parts/NotificationPoliciesSelect';

const cx = cn.bind(styles);

type TeamResponderProps = ResponderBaseProps & Pick<TeamResponderType, 'important' | 'data'>;

const TeamResponder: FC<TeamResponderProps> = ({
  important,
  data: { avatar_url, name },
  onImportantChange,
  handleDelete,
}) => (
  <li>
    <HorizontalGroup justify="space-between">
      <HorizontalGroup>
        <div className={cx('timeline-icon-background')}>
          <Avatar size="medium" src={avatar_url} />
        </div>
        <Text className={cx('responder-name')}>{name}</Text>
      </HorizontalGroup>
      <HorizontalGroup>
        <NotificationPoliciesSelect important={important} onChange={onImportantChange} />
        <IconButton
          data-testid="team-responder-delete-icon"
          tooltip="Remove responder"
          name="trash-alt"
          onClick={handleDelete}
        />
      </HorizontalGroup>
    </HorizontalGroup>
  </li>
);

export default TeamResponder;
