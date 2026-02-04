import React, { useCallback } from 'react';

import { Button, InlineField, Input, Stack } from '@grafana/ui';
import { StackSize } from 'helpers/consts';
import { observer } from 'mobx-react';

import { WithConfirm } from 'components/WithConfirm/WithConfirm';
import { UserSettingsTab } from 'containers/UserSettings/UserSettings.types';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useStore } from 'state/useStore';

interface ZoomConnectorProps {
  id: ApiSchemas['User']['pk'];
  onTabChange: (tab: UserSettingsTab) => void;
}
export const ZoomConnector = observer((props: ZoomConnectorProps) => {
  const { id, onTabChange } = props;

  const store = useStore();
  const { userStore } = store;

  const storeUser = userStore.items[id];

  const isCurrentUser = id === store.userStore.currentUserPk;

  const handleConnectButtonClick = useCallback(() => {
    onTabChange(UserSettingsTab.ZoomInfo);
  }, [onTabChange]);

  const handleUnlinkZoomAccount = useCallback(() => {
    userStore.unlinkBackend(id, 'ZOOM');
  }, [userStore, id]);

  const zoomConfigured = storeUser.messaging_backends['ZOOM'] as { display_name?: string; email?: string } | undefined;

  return (
    <div>
      {storeUser.messaging_backends.ZOOM ? (
        <InlineField label="Zoom" labelWidth={12}>
          <Stack gap={StackSize.xs}>
            <Input disabled={true} value={zoomConfigured?.display_name || zoomConfigured?.email || ''} />
            <WithConfirm title="Are you sure to disconnect your Zoom account?" confirmText="Disconnect">
              <Button
                disabled={!isCurrentUser}
                variant="destructive"
                icon="times"
                onClick={handleUnlinkZoomAccount}
                tooltip={'Unlink Zoom Account'}
              />
            </WithConfirm>
          </Stack>
        </InlineField>
      ) : (
        <div>
          <InlineField label="Zoom" labelWidth={12} disabled={!isCurrentUser}>
            <Button onClick={handleConnectButtonClick}>Connect account</Button>
          </InlineField>
        </div>
      )}
    </div>
  );
});
