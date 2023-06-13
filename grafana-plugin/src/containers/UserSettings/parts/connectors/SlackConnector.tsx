import React, { useCallback } from 'react';

import { Button, Label } from '@grafana/ui';
import cn from 'classnames/bind';

import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import { UserSettingsTab } from 'containers/UserSettings/UserSettings.types';
import { User } from 'models/user/user.types';
import { useStore } from 'state/useStore';

import styles from './index.module.css';

const cx = cn.bind(styles);

interface SlackConnectorProps {
  id: User['pk'];
  onTabChange: (tab: UserSettingsTab) => void;
}

const SlackConnector = (props: SlackConnectorProps) => {
  const { id, onTabChange } = props;

  const store = useStore();
  const { userStore, teamStore } = store;

  const storeUser = userStore.items[id];

  const isCurrent = id === store.userStore.currentUserPk;

  const handleConnectButtonClick = useCallback(() => {
    onTabChange(UserSettingsTab.SlackInfo);
  }, [onTabChange]);

  const handleUnlinkSlackAccount = useCallback(() => {
    userStore.unlinkSlack(userStore.currentUserPk);
  }, []);

  return (
    <div className={cx('user-item')}>
      <Label>Slack username:</Label>
      <span className={cx('user-value')}>{storeUser.slack_user_identity?.name || '—'}</span>
      {storeUser.slack_user_identity ? (
        <div>
          <Text type="secondary"> Slack account is connected</Text>
          {storeUser.pk === userStore.currentUserPk ? (
            <WithConfirm title="Are you sure to disconnect your Slack account?" confirmText="Disconnect">
              <Button size="sm" fill="text" variant="destructive" onClick={handleUnlinkSlackAccount}>
                Unlink Slack account
              </Button>
            </WithConfirm>
          ) : (
            ''
          )}
        </div>
      ) : teamStore.currentTeam?.slack_team_identity ? (
        <div>
          <Text type="warning">Slack account is not connected</Text>
          {isCurrent && (
            <Button size="sm" fill="text" onClick={handleConnectButtonClick}>
              Connect
            </Button>
          )}
        </div>
      ) : (
        <div>
          <Text type="warning">Slack Integration is not installed</Text>
          <PluginLink query={{ page: 'chat-ops' }}>
            <Button size="sm" fill="text">
              Install
            </Button>
          </PluginLink>
        </div>
      )}
    </div>
  );
};

export default SlackConnector;
