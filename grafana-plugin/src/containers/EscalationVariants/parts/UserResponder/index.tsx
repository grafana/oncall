import React, { FC } from 'react';

import { HorizontalGroup, IconButton } from '@grafana/ui';
import cn from 'classnames/bind';

import Avatar from 'components/Avatar/Avatar';
import Text from 'components/Text/Text';
import styles from 'containers/EscalationVariants/EscalationVariants.module.scss';
import {
  ResponderBaseProps,
  UserResponder as UserResponderType,
} from 'containers/EscalationVariants/EscalationVariants.types';
import NotificationPoliciesSelect from 'containers/EscalationVariants/parts/NotificationPoliciesSelect';

const cx = cn.bind(styles);

type UserResponderProps = ResponderBaseProps &
  Pick<UserResponderType, 'important' | 'data'> & {
    disableNotificationPolicySelect?: boolean;
  };

const UserResponder: FC<UserResponderProps> = ({
  important,
  data: { avatar, username },
  onImportantChange,
  handleDelete,
  disableNotificationPolicySelect = false,
}) => (
  <li>
    <HorizontalGroup justify="space-between">
      <HorizontalGroup>
        <div className={cx('timeline-icon-background', { 'timeline-icon-background--green': true })}>
          <Avatar size="medium" src={avatar} />
        </div>
        <Text className={cx('responder-name')}>{username}</Text>
      </HorizontalGroup>
      <HorizontalGroup>
        <NotificationPoliciesSelect
          disabled={disableNotificationPolicySelect}
          important={important}
          onChange={onImportantChange}
        />
        <IconButton
          data-testid="user-responder-delete-icon"
          tooltip="Remove responder"
          name="trash-alt"
          onClick={handleDelete}
        />
      </HorizontalGroup>
    </HorizontalGroup>
  </li>
);

export default UserResponder;
