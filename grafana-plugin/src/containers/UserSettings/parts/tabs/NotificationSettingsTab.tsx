import React, { useEffect } from 'react';

import PersonalNotificationSettings from 'containers/PersonalNotificationSettings/PersonalNotificationSettings';
import { User } from 'models/user/user.types';
import { useStore } from 'state/useStore';

export const NotificationSettingsTab = (props: { id: User['pk'] }) => {
  const { id } = props;

  const store = useStore();

  const { userStore } = store;

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
