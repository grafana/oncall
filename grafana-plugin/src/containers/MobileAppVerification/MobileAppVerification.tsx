import React, { HTMLAttributes, useEffect, useState } from 'react';

import { Button, LoadingPlaceholder } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import Text from 'components/Text/Text';
import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { User } from 'models/user/user.types';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization';

import styles from './MobileAppVerification.module.css';

const cx = cn.bind(styles);

interface MobileAppVerificationProps extends HTMLAttributes<HTMLElement> {
  userPk?: User['pk'];
  phone?: string;
}

const MobileAppVerification = observer((props: MobileAppVerificationProps) => {
  const { userPk: propsUserPk } = props;

  const store = useStore();
  const { userStore } = store;

  const userPk = (propsUserPk || userStore.currentUserPk) as User['pk'];
  const user = userStore.items[userPk as User['pk']];
  const isCurrent = userStore.currentUserPk === user.pk;
  const action = isCurrent ? UserActions.UserSettingsWrite : UserActions.OtherSettingsWrite;

  const [showMobileAppVerificationToken, setShowMobileAppVerificationToken] = useState<string>(undefined);
  const [isMobileAppVerificationTokenExisting, setIsMobileAppVerificationTokenExisting] = useState<boolean>(false);
  const [MobileAppVerificationTokenLoading, setMobileAppVerificationTokenLoading] = useState<boolean>(true);

  useEffect(() => {
    userStore
      .getMobileAppVerificationToken(userPk)
      .then((_res) => {
        setIsMobileAppVerificationTokenExisting(true);
        setMobileAppVerificationTokenLoading(false);
      })
      .catch((_res) => {
        setIsMobileAppVerificationTokenExisting(false);
        setMobileAppVerificationTokenLoading(false);
      });
  }, []);

  const handleCreateMobileAppVerificationToken = async () => {
    setIsMobileAppVerificationTokenExisting(true);
    await userStore
      .createMobileAppVerificationToken(userPk)
      .then((res) => setShowMobileAppVerificationToken(res?.token));
  };

  return (
    <div className={cx('mobile-app-settings')}>
      {MobileAppVerificationTokenLoading ? (
        <LoadingPlaceholder text="Loading..." />
      ) : (
        <>
          <p>
            <Text>Open Grafana OnCall mobile application and enter the following code to add the new device:</Text>
          </p>
          {isMobileAppVerificationTokenExisting ? (
            <>
              {showMobileAppVerificationToken !== undefined ? (
                <>
                  <h1>{showMobileAppVerificationToken}</h1>
                  <p>
                    <Text>* This code is active only for a minute</Text>
                  </p>
                  <p>
                    <WithPermissionControl userAction={action}>
                      <Button
                        onClick={handleCreateMobileAppVerificationToken}
                        className={cx('iCal-button')}
                        variant="secondary"
                      >
                        Refresh the code
                      </Button>
                    </WithPermissionControl>
                  </p>
                </>
              ) : (
                <></>
              )}
            </>
          ) : (
            <p>
              <WithPermissionControl userAction={action}>
                <Button
                  onClick={handleCreateMobileAppVerificationToken}
                  className={cx('iCal-button')}
                  variant="secondary"
                >
                  Get the code
                </Button>
              </WithPermissionControl>
            </p>
          )}
          <p>
            <Text>* Only iOS is currently supported</Text>
          </p>
        </>
      )}
    </div>
  );
});

export default MobileAppVerification;
