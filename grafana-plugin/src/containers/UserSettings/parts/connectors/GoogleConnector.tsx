import React, { useCallback } from 'react';

import { Button, HorizontalGroup, InlineField, Input } from '@grafana/ui';

import { WithConfirm } from 'components/WithConfirm/WithConfirm';
import { UserSettingsTab } from 'containers/UserSettings/UserSettings.types';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useStore } from 'state/useStore';

interface GoogleConnectorProps {
  id: ApiSchemas['User']['pk'];
  onTabChange: (tab: UserSettingsTab) => void;
}

export const GoogleConnector = (props: GoogleConnectorProps) => {
  const { id, onTabChange } = props;

  const store = useStore();
  const { userStore } = store;

  const storeUser = userStore.items[id];

  const isCurrentUser = id === store.userStore.currentUserPk;

  const handleConnectButtonClick = useCallback(() => {
    onTabChange(UserSettingsTab.GoogleCalendar);
  }, [onTabChange]);

  const handleUnlinkGoogleAccount = useCallback(() => {
    userStore.unlinkGoogle(userStore.currentUserPk);
  }, []);

  return (
    <div>
      <InlineField label="Google Account" labelWidth={15}>
        {storeUser.has_google_oauth2_connected ? (
          <HorizontalGroup spacing="xs">
            <Input disabled value={'google_username_here'} />
            <WithConfirm title="Are you sure to disconnect your Google account?" confirmText="Disconnect">
              <Button
                onClick={handleUnlinkGoogleAccount}
                variant="destructive"
                icon="times"
                disabled={!isCurrentUser}
              />
            </WithConfirm>
          </HorizontalGroup>
        ) : (
          <Button disabled={!isCurrentUser} onClick={handleConnectButtonClick}>
            Connect account
          </Button>
        )}
      </InlineField>
    </div>
  );
};
