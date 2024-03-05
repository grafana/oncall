import React from 'react';

import { Tooltip } from '@grafana/ui';
import { observer } from 'mobx-react';

import { UserHelper } from 'models/user/user.helpers';

import { useStore } from 'state/useStore';
import { ApiSchemas } from 'network/oncall-api/api.types';

interface UserTooltipProps {
  id: ApiSchemas['User']['pk'];
}

export const UserTooltip = observer((props: UserTooltipProps) => {
  const { id } = props;

  const store = useStore();

  const { userStore } = store;

  const user = userStore.items[id];

  return (
    <Tooltip content={UserHelper.getUserNotificationsSummary(user)}>
      <span>{user?.username}</span>
    </Tooltip>
  );
});
