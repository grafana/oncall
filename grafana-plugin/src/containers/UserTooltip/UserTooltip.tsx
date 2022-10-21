import React from 'react';

import { Tooltip } from '@grafana/ui';
import { observer } from 'mobx-react';

import { getUserNotificationsSummary } from 'models/user/user.helpers';
import { User } from 'models/user/user.types';
import { useStore } from 'state/useStore';

interface UserTooltipProps {
  id: User['pk'];
}

const UserTooltip = observer(({ id }: UserTooltipProps) => {
  const { userStore } = useStore();
  const user = userStore.items[id];

  return (
    <Tooltip content={getUserNotificationsSummary(user)}>
      <span>{user?.username}</span>
    </Tooltip>
  );
});

export default UserTooltip;
