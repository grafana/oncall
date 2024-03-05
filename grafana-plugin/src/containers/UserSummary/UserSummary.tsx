import { useEffect } from 'react';

import { observer } from 'mobx-react';

import { UserHelper } from 'models/user/user.helpers';
import { User } from 'models/user/user.types';
import { useStore } from 'state/useStore';

interface UserSummaryProps {
  id: User['pk'];
}

export const UserSummary = observer((props: UserSummaryProps) => {
  const { id } = props;

  const store = useStore();

  const { userStore } = store;

  useEffect(() => {
    if (!userStore.items[id]) {
      userStore.fetchItemById(id);
    }
  });

  const user = userStore.items[id];

  return UserHelper.getUserNotificationsSummary(user);
});
