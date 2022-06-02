import React, { useCallback } from 'react';

import { Button, Label } from '@grafana/ui';
import cn from 'classnames/bind';

import Text from 'components/Text/Text';
import { UserSettingsTab } from 'containers/UserSettings/UserSettings.types';
import { User } from 'models/user/user.types';
import { useStore } from 'state/useStore';

import styles from './index.module.css';

const cx = cn.bind(styles);

interface PhoneConnectorProps {
  id: User['pk'];
  onTabChange: (tab: UserSettingsTab) => void;
}

const PhoneConnector = (props: PhoneConnectorProps) => {
  const { id, onTabChange } = props;

  const store = useStore();
  const { userStore } = store;

  const storeUser = userStore.items[id];

  const handleClickConfirmPhoneButton = useCallback(() => {
    onTabChange(UserSettingsTab.PhoneVerification);
  }, [storeUser?.unverified_phone_number]);

  return (
    <div className={cx('user-item')}>
      <Label>Verified phone number:</Label>
      <span className={cx('user-value')}>{storeUser.verified_phone_number || '—'}</span>
      {storeUser.verified_phone_number ? (
        <div>
          <Text type="secondary">Phone number is verified</Text>
          <Button size="sm" fill="text" onClick={handleClickConfirmPhoneButton}>
            Change
          </Button>
        </div>
      ) : storeUser.unverified_phone_number ? (
        <div>
          <Text type="warning">Phone number is not verified</Text>
          <Button size="sm" fill="text" onClick={handleClickConfirmPhoneButton}>
            Verify or change
          </Button>
        </div>
      ) : (
        <div>
          <Text type="warning">Phone number is not added</Text>
          <Button size="sm" fill="text" onClick={handleClickConfirmPhoneButton}>
            Add
          </Button>
        </div>
      )}
    </div>
  );
};

export default PhoneConnector;
