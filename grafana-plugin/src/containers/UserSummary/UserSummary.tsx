import { useEffect } from 'react';

import { observer } from 'mobx-react';

import { getUserNotificationsSummary } from 'models/user/user.helpers';
import { User } from 'models/user/user.types';
import { useStore } from 'state/useStore';

interface UserSummaryProps {
  id: User['pk'];
}

const UserSummary = observer(({ id }: UserSummaryProps) => {
  const { userStore } = useStore();
  const user = userStore.items[id];

  useEffect(() => {
    if (!userStore.items[id]) {
      userStore.loadUser(id);
    }
  });

  return getUserNotificationsSummary(user);
});

export default UserSummary;
