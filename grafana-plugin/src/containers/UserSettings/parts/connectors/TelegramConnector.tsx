import React, { useCallback } from 'react';

import { Button, Label } from '@grafana/ui';
import cn from 'classnames/bind';

import Text from 'components/Text/Text';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import { UserSettingsTab } from 'containers/UserSettings/UserSettings.types';
import { User } from 'models/user/user.types';
import { useStore } from 'state/useStore';

import styles from './index.module.css';

const cx = cn.bind(styles);

interface TelegramConnectorProps {
  id: User['pk'];
  onTabChange: (tab: UserSettingsTab) => void;
}

const TelegramConnector = (props: TelegramConnectorProps) => {
  const { id, onTabChange } = props;

  const store = useStore();
  const { userStore } = store;

  const storeUser = userStore.items[id];

  const isCurrent = id === store.userStore.currentUserPk;

  const handleConnectButtonClick = useCallback(() => {
    onTabChange(UserSettingsTab.TelegramInfo);
  }, [onTabChange]);

  const handleUnlinkTelegramAccount = useCallback(() => {
    userStore.unlinkTelegram(userStore.currentUserPk);
  }, []);

  return (
    <div className={cx('user-item')}>
      <Label>Telegram username:</Label>
      <span className={cx('user-value')}>{storeUser.telegram_configuration?.telegram_nick_name || '—'}</span>
      {storeUser.telegram_configuration && storeUser.pk === userStore.currentUserPk ? (
        <div>
          <Text type="secondary"> Telegram account is connected</Text>
          {storeUser.pk === userStore.currentUserPk ? (
            <WithConfirm title="Are you sure to disconnect your Telegram account?" confirmText="Disconnect">
              <Button size="sm" fill="text" variant="destructive" onClick={handleUnlinkTelegramAccount}>
                Unlink Telegram account
              </Button>
            </WithConfirm>
          ) : (
            ''
          )}
        </div>
      ) : (
        <div>
          <Text type="warning">Telegram account is not connected</Text>
          {isCurrent && (
            <Button size="sm" fill="text" onClick={handleConnectButtonClick}>
              Connect
            </Button>
          )}
        </div>
      )}
    </div>
  );
};

export default TelegramConnector;
