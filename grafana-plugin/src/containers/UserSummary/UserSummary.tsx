import { useEffect } from 'react';

import { observer } from 'mobx-react';

import { UserHelper } from 'models/user/user.helpers';

import { useStore } from 'state/useStore';
import { ApiSchemas } from 'network/oncall-api/api.types';

interface UserSummaryProps {
  id: ApiSchemas['User']['pk'];
}

export const UserSummary = observer((props: UserSummaryProps) => {
  const { id } = props;

  const store = useStore();

  const { userStore } = store;

  useEffect(() => {
    if (!userStore.items[id]) {
      userStore.fetchItemById({ userPk: id });
    }
  });

  const user = userStore.items[id];

  return UserHelper.getUserNotificationsSummary(user);
});
