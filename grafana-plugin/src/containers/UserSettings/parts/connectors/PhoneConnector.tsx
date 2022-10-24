import React, { useCallback } from 'react';

import { Button, Label, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';

import Text from 'components/Text/Text';
import { UserSettingsTab } from 'containers/UserSettings/UserSettings.types';
import { User } from 'models/user/user.types';
import { AppFeature } from 'state/features';
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
  }, [storeUser?.unverified_phone_number, onTabChange]);

  const cloudVersionPhone = (user: User) => {
    switch (user.cloud_connection_status) {
      case 0:
        return <Text className={cx('error-message')}>Cloud is not synced</Text>;

      case 1:
        return (
          <VerticalGroup>
            <Text className={cx('error-message')}>User is not matched with cloud</Text>
            <Button size="sm" fill="text" onClick={handleClickConfirmPhoneButton}>
              Sign Up to Cloud
            </Button>
          </VerticalGroup>
        );

      case 2:
        return (
          <VerticalGroup>
            <Text type="warning">Phone number is not verified in Grafana Cloud</Text>
            <Button size="sm" fill="text" onClick={handleClickConfirmPhoneButton}>
              Verify or change
            </Button>
          </VerticalGroup>
        );
      case 3:
        return (
          <VerticalGroup>
            <Text type="success">Phone number verified</Text>
            <Button size="sm" fill="text" onClick={handleClickConfirmPhoneButton}>
              Change
            </Button>
          </VerticalGroup>
        );
      default:
        return (
          <VerticalGroup>
            <Text className={cx('error-message')}>User is not matched with cloud</Text>
            <Button size="sm" fill="text" onClick={handleClickConfirmPhoneButton}>
              Sign Up to Cloud
            </Button>
          </VerticalGroup>
        );
    }
  };

  return (
    <div className={cx('user-item')}>
      {store.hasFeature(AppFeature.CloudNotifications) ? (
        <>
          <Label>Cloud phone status:</Label>
          {cloudVersionPhone(storeUser)}
        </>
      ) : (
        <>
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
        </>
      )}
    </div>
  );
};

export default PhoneConnector;
