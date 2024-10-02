import React, { useCallback } from 'react';

import { Button, InlineField, Input, Stack } from '@grafana/ui';
import { StackSize } from 'helpers/consts';
import { observer } from 'mobx-react';

import { WithConfirm } from 'components/WithConfirm/WithConfirm';
import { UserSettingsTab } from 'containers/UserSettings/UserSettings.types';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useStore } from 'state/useStore';

interface TelegramConnectorProps {
  id: ApiSchemas['User']['pk'];
  onTabChange: (tab: UserSettingsTab) => void;
}

export const TelegramConnector = observer((props: TelegramConnectorProps) => {
  const { id, onTabChange } = props;

  const store = useStore();
  const { userStore } = store;

  const storeUser = userStore.items[id];

  const isCurrentUser = id === store.userStore.currentUserPk;

  const handleConnectButtonClick = useCallback(() => {
    onTabChange(UserSettingsTab.TelegramInfo);
  }, [onTabChange]);

  const handleUnlinkTelegramAccount = useCallback(() => {
    userStore.unlinkTelegram(userStore.currentUserPk);
  }, []);

  return (
    <div>
      <InlineField label="Telegram" labelWidth={12} disabled={!isCurrentUser}>
        {storeUser.telegram_configuration ? (
          <Stack gap={StackSize.xs}>
            <Input
              disabled={true}
              value={
                storeUser.telegram_configuration?.telegram_nick_name
                  ? '@' + storeUser.telegram_configuration?.telegram_nick_name
                  : ''
              }
            />
            <WithConfirm title="Are you sure to disconnect your Telegram account?" confirmText="Disconnect">
              <Button
                onClick={handleUnlinkTelegramAccount}
                variant="destructive"
                icon="times"
                disabled={!isCurrentUser}
              />
            </WithConfirm>
          </Stack>
        ) : (
          <Button onClick={handleConnectButtonClick}>Connect account</Button>
        )}
      </InlineField>
    </div>
  );
});
