import { HorizontalGroup } from '@grafana/ui';
import Avatar from 'components/Avatar/Avatar';
import Text from 'components/Text/Text';
import { User } from 'models/user/user.types';
import React, { useEffect, useState } from 'react';
import { useStore } from 'state/useStore';

interface UserDisplayProps {
  id: User['pk'];
}

const UserDisplayWithAvatar: React.FC<UserDisplayProps> = ({ id }) => {
  const { userStore } = useStore();
  const [user, setUser] = useState<User>(undefined);

  useEffect(() => {
    (async function () {
      if (!userStore.items[id]) {
        await userStore.updateItem(id);
        setUser(userStore.items[id]);
      }
    })();
  }, [id]);

  if (!user) return null;

  return (
    <HorizontalGroup spacing="xs">
      <Avatar size="small" src={user.avatar}></Avatar>
      <Text type="secondary">{user.email}</Text>
    </HorizontalGroup>
  );
};

export default UserDisplayWithAvatar;
