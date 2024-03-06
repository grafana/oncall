import React, { useEffect } from 'react';

import { PersonalNotificationSettings } from 'containers/PersonalNotificationSettings/PersonalNotificationSettings';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useStore } from 'state/useStore';

export const NotificationSettingsTab = (props: { id: ApiSchemas['User']['pk'] }) => {
  const { id } = props;

  const store = useStore();

  const { userStore } = store;

  useEffect(() => {
    userStore.updateNotificationPolicies(id);
  }, [userStore, id]);

  return (
    <div>
      <div data-testid="default-personal-notification-settings">
        <PersonalNotificationSettings userPk={id} isImportant={false} />
      </div>
      <div data-testid="important-personal-notification-settings">
        <PersonalNotificationSettings userPk={id} isImportant={true} />
      </div>
    </div>
  );
};
