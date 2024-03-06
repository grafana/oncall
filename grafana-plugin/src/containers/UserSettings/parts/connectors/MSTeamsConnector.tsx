import React, { useCallback } from 'react';

import { Button, HorizontalGroup, InlineField, Input } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import { WithConfirm } from 'components/WithConfirm/WithConfirm';
import { UserSettingsTab } from 'containers/UserSettings/UserSettings.types';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useStore } from 'state/useStore';

import styles from 'containers/UserSettings/parts/connectors/Connectors.module.css';

const cx = cn.bind(styles);

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

  const handleUnlinkMSTeamsAccount = useCallback(() => {
    userStore.unlinkBackend(id, 'MSTEAMS');
  }, []);

  return (
    <div className={cx('user-item')}>
      {storeUser.messaging_backends.MSTEAMS ? (
        <InlineField label="MS Teams" labelWidth={12}>
          <HorizontalGroup spacing="xs">
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
          </HorizontalGroup>
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
