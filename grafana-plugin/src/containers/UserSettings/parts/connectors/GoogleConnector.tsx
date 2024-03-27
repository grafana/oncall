import React, { useCallback } from 'react';

import { Button, HorizontalGroup, InlineField } from '@grafana/ui';
import { observer } from 'mobx-react';

import { WithConfirm } from 'components/WithConfirm/WithConfirm';
import { UserHelper } from 'models/user/user.helpers';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useStore } from 'state/useStore';

interface GoogleConnectorProps {
  id: ApiSchemas['User']['pk'];
}

export const GoogleConnector = observer((props: GoogleConnectorProps) => {
  const { id } = props;

  const store = useStore();
  const { userStore } = store;

  const storeUser = userStore.items[id];

  const isCurrentUser = id === store.userStore.currentUserPk;

  const handleConnectButtonClick = useCallback(() => {
    UserHelper.handleConnectGoogle();
  }, []);

  const handleUnlinkGoogleAccount = useCallback(() => {
    userStore.disconnectGoogle();
  }, []);

  return (
    <div>
      <InlineField label="Google Account" labelWidth={15}>
        {storeUser.has_google_oauth2_connected ? (
          <HorizontalGroup spacing="xs">
            <WithConfirm title="Are you sure to disconnect your Google account?" confirmText="Disconnect">
              <Button disabled={!isCurrentUser} variant="destructive" onClick={handleUnlinkGoogleAccount}>
                Disconnect
              </Button>
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
});
