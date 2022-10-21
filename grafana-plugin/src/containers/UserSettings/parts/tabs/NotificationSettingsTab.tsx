import React, { useEffect } from 'react';

import PersonalNotificationSettings from 'containers/PersonalNotificationSettings/PersonalNotificationSettings';
import { User } from 'models/user/user.types';
import { useStore } from 'state/useStore';

type Props = {
  id: User['pk'];
};

export const NotificationSettingsTab = ({ id }: Props) => {
  const { userStore } = useStore();

  useEffect(() => {
    userStore.updateNotificationPolicies(id);
  }, [userStore, id]);

  return (
    <div>
      <PersonalNotificationSettings userPk={id} isImportant={false} />
      <PersonalNotificationSettings userPk={id} isImportant={true} />
    </div>
  );
};
