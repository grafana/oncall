import React, { FC } from 'react';

import { SelectableValue } from '@grafana/data';
import { ActionMeta, HorizontalGroup, IconButton } from '@grafana/ui';
import cn from 'classnames/bind';

import Avatar from 'components/Avatar/Avatar';
import Text from 'components/Text/Text';
import styles from 'containers/AddResponders/AddResponders.module.scss';
import { UserResponder as UserResponderType } from 'containers/AddResponders/AddResponders.types';
import NotificationPoliciesSelect from 'containers/AddResponders/parts/NotificationPoliciesSelect/NotificationPoliciesSelect';

const cx = cn.bind(styles);

type Props = UserResponderType & {
  onImportantChange: (value: SelectableValue<number>, actionMeta: ActionMeta) => void | {};
  handleDelete: React.MouseEventHandler<HTMLButtonElement>;
  disableNotificationPolicySelect?: boolean;
};

const UserResponder: FC<Props> = ({
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
