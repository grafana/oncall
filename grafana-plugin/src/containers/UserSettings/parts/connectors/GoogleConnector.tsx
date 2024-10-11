import React from 'react';

import { Button, InlineField, Stack } from '@grafana/ui';
import { UserActions } from 'helpers/authorization/authorization';
import { StackSize } from 'helpers/consts';
import { observer } from 'mobx-react';

import { WithConfirm } from 'components/WithConfirm/WithConfirm';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
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

  return (
    <div>
      <InlineField label="Google Account" labelWidth={15}>
        {storeUser.has_google_oauth2_connected ? (
          <Stack gap={StackSize.xs}>
            <WithPermissionControlTooltip userAction={UserActions.UserSettingsWrite}>
              <WithConfirm title="Are you sure to disconnect your Google account?" confirmText="Disconnect">
                <Button disabled={!isCurrentUser} variant="destructive" onClick={userStore.disconnectGoogle}>
                  Disconnect
                </Button>
              </WithConfirm>
            </WithPermissionControlTooltip>
          </Stack>
        ) : (
          <WithPermissionControlTooltip userAction={UserActions.UserSettingsWrite}>
            <Button disabled={!isCurrentUser} onClick={UserHelper.handleConnectGoogle}>
              Connect account
            </Button>
          </WithPermissionControlTooltip>
        )}
      </InlineField>
    </div>
  );
});
