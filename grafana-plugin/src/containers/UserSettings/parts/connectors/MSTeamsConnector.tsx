import React, { useCallback } from 'react';

import { Button, InlineField, Input, Stack, useStyles2 } from '@grafana/ui';
import { StackSize } from 'helpers/consts';
import { observer } from 'mobx-react';

import { WithConfirm } from 'components/WithConfirm/WithConfirm';
import { getConnectorsStyles } from 'containers/AlertRules/parts/connectors/Connectors.styles';
import { UserSettingsTab } from 'containers/UserSettings/UserSettings.types';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useStore } from 'state/useStore';

interface MSTeamsConnectorProps {
  id: ApiSchemas['User']['pk'];
  onTabChange: (tab: UserSettingsTab) => void;
}

export const MSTeamsConnector = observer((props: MSTeamsConnectorProps) => {
  const { id, onTabChange } = props;

  const store = useStore();
  const { userStore } = store;

  const storeUser = userStore.items[id];

  const isCurrentUser = id === store.userStore.currentUserPk;

  const handleConnectButtonClick = useCallback(() => {
    onTabChange(UserSettingsTab.MSTeamsInfo);
  }, []);

  const styles = useStyles2(getConnectorsStyles);

  const handleUnlinkMSTeamsAccount = useCallback(() => {
    userStore.unlinkBackend(id, 'MSTEAMS');
  }, []);

  return (
    <div className={styles.userItem}>
      {storeUser.messaging_backends.MSTEAMS ? (
        <InlineField label="MS Teams" labelWidth={12}>
          <Stack gap={StackSize.xs}>
            <Input disabled={true} value={(storeUser.messaging_backends.MSTEAMS?.name as string) || '—'} />
            <WithConfirm title="Are you sure to disconnect your Microsoft Teams account?" confirmText="Disconnect">
              <Button
                disabled={!isCurrentUser}
                variant="destructive"
                icon="times"
                onClick={handleUnlinkMSTeamsAccount}
                tooltip={'Unlink MS Teams Account'}
              />
            </WithConfirm>
          </Stack>
        </InlineField>
      ) : (
        <div>
          <InlineField label="MS Teams" labelWidth={12} disabled={!isCurrentUser}>
            <Button onClick={handleConnectButtonClick}>Connect account</Button>
          </InlineField>
        </div>
      )}
    </div>
  );
});
