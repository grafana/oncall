import React from 'react';

import { Label } from '@grafana/ui';
import cn from 'classnames/bind';

import Text from 'components/Text/Text';
import { UserSettingsTab } from 'containers/UserSettings/UserSettings.types';
import { Connectors } from 'containers/UserSettings/parts/connectors';
import { User } from 'models/user/user.types';
import { useStore } from 'state/useStore';

import styles from './UserInfoTab.module.css';

const cx = cn.bind(styles);

interface UserInfoTabProps {
  id: User['pk'];
  onTabChange: (tab: UserSettingsTab) => void;
}

export const UserInfoTab = (props: UserInfoTabProps) => {
  const { id } = props;

  const store = useStore();
  const { userStore } = store;

  const storeUser = userStore.items[id];

  return (
    <>
      <div className={cx('user-item')}>
        <Text type="secondary">
          To edit user details such as Username, email, and roles, please visit{' '}
          <a href="/org/users"> Grafana User settings</a>.
        </Text>
      </div>
      <div className={cx('user-item')}>
        <Label>Username:</Label>
        <span className={cx('user-value')}>{storeUser.username || '—'}</span>
      </div>
      <div className={cx('user-item')}>
        <Label>Email:</Label>
        <span className={cx('user-value')}>{storeUser.email || '—'}</span>
      </div>
      <Connectors {...props} />
    </>
  );
};
