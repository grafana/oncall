import React from 'react';

import { Tooltip } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import { getUserNotificationsSummary } from 'models/user/user.helpers';
import { User } from 'models/user/user.types';
import { useStore } from 'state/useStore';

import styles from 'containers/UserTooltip/UserTooltip.module.css';

const cx = cn.bind(styles);

interface UserTooltipProps {
  id: User['pk'];
}

const UserTooltip = observer((props: UserTooltipProps) => {
  const { id } = props;

  const store = useStore();

  const { userStore } = store;

  const user = userStore.items[id];

  return (
    <Tooltip content={getUserNotificationsSummary(user)}>
      <span>{user?.username}</span>
    </Tooltip>
  );
});

export default UserTooltip;
