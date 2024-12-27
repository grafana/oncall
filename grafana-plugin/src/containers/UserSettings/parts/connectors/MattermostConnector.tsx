import React, { useCallback } from 'react';

import { Button, InlineField, Input, Stack } from '@grafana/ui';
import { StackSize } from 'helpers/consts';
import { observer } from 'mobx-react';

import { WithConfirm } from 'components/WithConfirm/WithConfirm';
import { UserSettingsTab } from 'containers/UserSettings/UserSettings.types';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useStore } from 'state/useStore';

interface MattermostConnectorProps {
  id: ApiSchemas['User']['pk'];
  onTabChange: (tab: UserSettingsTab) => void;
}
export const MattermostConnector = observer((props: MattermostConnectorProps) => {
  const { id, onTabChange } = props;

  const store = useStore();
  const { userStore } = store;

  const storeUser = userStore.items[id];

  const isCurrentUser = id === store.userStore.currentUserPk;

  const handleConnectButtonClick = useCallback(() => {
    onTabChange(UserSettingsTab.MattermostInfo);
  }, []);

  const handleUnlinkMattermostAccount = useCallback(() => {
    userStore.unlinkBackend(id, 'MATTERMOST');
  }, []);

  const mattermostConfigured = storeUser.messaging_backends['MATTERMOST'];

  return (
    <div>
      {storeUser.messaging_backends.MATTERMOST ? (
        <InlineField label="Mattermost" labelWidth={12}>
          <Stack gap={StackSize.xs}>
            <Input disabled={true} value={mattermostConfigured?.username ? '@' + mattermostConfigured?.username : ''} />
            <WithConfirm title="Are you sure to disconnect your Mattermost account?" confirmText="Disconnect">
              <Button
                disabled={!isCurrentUser}
                variant="destructive"
                icon="times"
                onClick={handleUnlinkMattermostAccount}
                tooltip={'Unlink Mattermost Account'}
              />
            </WithConfirm>
          </Stack>
        </InlineField>
      ) : (
        <div>
          <InlineField label="Mattermost" labelWidth={12} disabled={!isCurrentUser}>
            <Button onClick={handleConnectButtonClick}>Connect account</Button>
          </InlineField>
        </div>
      )}
    </div>
  );
});
