import React, { useCallback } from 'react';

import { Button, InlineField, Input, Stack } from '@grafana/ui';
import { StackSize } from 'helpers/consts';
import { observer } from 'mobx-react';

import { WithConfirm } from 'components/WithConfirm/WithConfirm';
import { UserSettingsTab } from 'containers/UserSettings/UserSettings.types';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useStore } from 'state/useStore';

interface PersonalWebhookConnectorProps {
  id: ApiSchemas['User']['pk'];
  onTabChange: (tab: UserSettingsTab) => void;
}

export const PersonalWebhookConnector = observer((props: PersonalWebhookConnectorProps) => {
  const { id, onTabChange } = props;

  const store = useStore();
  const { userStore } = store;

  const storeUser = userStore.items[id];
  const isCurrentUser = id === store.userStore.currentUserPk;

  const handleConnectButtonClick = useCallback(() => {
    onTabChange(UserSettingsTab.PersonalWebhookInfo);
  }, []);

  const handleUnlinkPersonalWebhook = useCallback(() => {
    userStore.removePersonalWebhook();
  }, []);

  return (
    <div>
      {storeUser.messaging_backends.WEBHOOK ? (
        <InlineField label="Webhook" labelWidth={12} disabled={!isCurrentUser}>
          <Stack gap={StackSize.xs}>
            <Input disabled={true} value={(storeUser.messaging_backends.WEBHOOK?.name as string) || '—'} />
            <WithConfirm title="Are you sure you want to disconnect your personal webhook?" confirmText="Disconnect">
              <Button
                disabled={!isCurrentUser}
                variant="destructive"
                icon="times"
                onClick={handleUnlinkPersonalWebhook}
                tooltip={'Unlink Personal Webhook'}
              />
            </WithConfirm>
          </Stack>
        </InlineField>
      ) : (
        <div>
          <InlineField label="Webhook" labelWidth={12} disabled={!isCurrentUser}>
            <Button onClick={handleConnectButtonClick}>Connect</Button>
          </InlineField>
        </div>
      )}
    </div>
  );
});
