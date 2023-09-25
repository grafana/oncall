import React from 'react';

import { InlineField, Input, Legend } from '@grafana/ui';

import { UserSettingsTab } from 'containers/UserSettings/UserSettings.types';
import { Connectors } from 'containers/UserSettings/parts/connectors';
import { User } from 'models/user/user.types';
import { useStore } from 'state/useStore';

import GrafanaTeamSelect from 'containers/GrafanaTeamSelect/GrafanaTeamSelect';

interface UserInfoTabProps {
  id: User['pk'];
  onTabChange: (tab: UserSettingsTab) => void;
}

export const UserInfoTab = (props: UserInfoTabProps) => {
  const { id } = props;

  const store = useStore();
  const { userStore } = store;

  const storeUser = userStore.items[id];
  let width = 15;

  return (
    <>
      <Legend>User information</Legend>
      <InlineField
        label="Username"
        labelWidth={width}
        grow
        disabled
        tooltip="To edit username go to Grafana user management"
      >
        <Input value={storeUser.username || ''} />
      </InlineField>
      <InlineField label="Email" labelWidth={width} grow disabled tooltip="To edit email go to Grafana user management">
        <Input value={storeUser.email || ''} />
      </InlineField>
      <InlineField label="Timezone" labelWidth={width} grow disabled>
        <Input value={storeUser.timezone || ''} />
      </InlineField>
      <InlineField 
        label="Default Team" 
        labelWidth={width} 
        grow
        tooltip="Default team will be pre-selected when you create new resources, such as integrations, schedules, etc."
      >
        <GrafanaTeamSelect withoutModal 
        defaultValue={storeUser.current_team}
        onSelect={async (value) => {
              await userStore.updateCurrentUser({ current_team: value });
              store.grafanaTeamStore.updateItems();
            }} />

      </InlineField>
      <Legend>Notification channels</Legend>
      <Connectors {...props} />
    </>
  );
};
