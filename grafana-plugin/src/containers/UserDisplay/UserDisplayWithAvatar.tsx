import React, { useEffect } from 'react';

import { HorizontalGroup } from '@grafana/ui';
import { observer } from 'mobx-react';

import Avatar from 'components/Avatar/Avatar';
import Text from 'components/Text/Text';
import { User } from 'models/user/user.types';
import { useStore } from 'state/useStore';

interface UserDisplayProps {
  id: User['pk'];
}

const UserDisplayWithAvatar = observer(({ id }: UserDisplayProps) => {
  const { userStore } = useStore();

  useEffect(() => {
    if (!userStore.items[id]) {
      userStore.updateItem(id);
    }
  }, [id]);

  const user = userStore.items[id];
  if (!user) {
    return null;
  }

  return (
    <HorizontalGroup spacing="xs">
      <Avatar size="small" src={user.avatar}></Avatar>
      <Text type="primary">{user.email}</Text>
    </HorizontalGroup>
  );
});

export default UserDisplayWithAvatar;
