import React, { useCallback } from 'react';

import { Button, InlineField } from '@grafana/ui';

import { UserSettingsTab } from 'containers/UserSettings/UserSettings.types';
import { User } from 'models/user/user.types';
import { useStore } from 'state/useStore';

interface MobileAppConnectorProps {
  id: User['pk'];
  onTabChange: (tab: UserSettingsTab) => void;
}

const MobileAppConnector = (props: MobileAppConnectorProps) => {
  const { onTabChange, id } = props;
  const store = useStore();
  const { userStore } = store;

  const handleClickConfirmMobileAppButton = useCallback(() => {
    onTabChange(UserSettingsTab.MobileAppConnection);
  }, [onTabChange]);

  const user = userStore.items[id];
  const isCurrentUser = id === store.userStore.currentUserPk;
  const isMobileAppConnected = user.messaging_backends['MOBILE_APP']?.connected;

  return (
    <InlineField label="Mobile App" labelWidth={12} disabled={!isCurrentUser}>
      {isMobileAppConnected ? (
        <Button variant="destructive" onClick={handleClickConfirmMobileAppButton}>
          Disconnect
        </Button>
      ) : (
        <Button onClick={handleClickConfirmMobileAppButton}>Connect</Button>
      )}
    </InlineField>
  );
};

export default MobileAppConnector;
