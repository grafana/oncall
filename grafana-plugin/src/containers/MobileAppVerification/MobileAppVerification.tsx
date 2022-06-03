import React, { HTMLAttributes, useCallback, useEffect, useRef, useState } from 'react';

import { Button, HorizontalGroup, Icon, LoadingPlaceholder } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import GTable from 'components/GTable/GTable';
import Text from 'components/Text/Text';
import { UserSettingsTab } from 'containers/UserSettings/UserSettings.types';
import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { User } from 'models/user/user.types';
import { makeRequest } from 'network';
import { useStore } from 'state/useStore';
import { UserAction } from 'state/userAction';

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

  const { id = UserSettingsTab.UserInfo } = props;

  const [showMobileAppVerificationToken, setShowMobileAppVerificationToken] = useState<string>(undefined);
  const [isMobileAppVerificationTokenExisting, setIsMobileAppVerificationTokenExisting] = useState<boolean>(false);
  const [MobileAppVerificationTokenLoading, setMobileAppVerificationTokenLoading] = useState<boolean>(true);

  useEffect(() => {
    userStore
      .getMobileAppVerificationToken(userPk)
      .then((res) => {
        setIsMobileAppVerificationTokenExisting(true);
        setMobileAppVerificationTokenLoading(false);
      })
      .catch((res) => {
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

  // const [devices, setDevices] = useState();
  //
  // const updateDevices = useCallback(() => {
  //   makeRequest(`/device/apns/`, {
  //     method: 'GET',
  //   }).then((data) => {
  //     setDevices(data);
  //   });
  // }, []);
  //
  // useEffect(() => {
  //   updateDevices();
  // }, []);
  //
  // const columns = [
  //   {
  //     title: 'Name',
  //     dataIndex: 'name',
  //   },
  // ];

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
                    <WithPermissionControl userAction={UserAction.UpdateOtherUsersSettings}>
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
            <>
              <p>
                <WithPermissionControl userAction={UserAction.UpdateOtherUsersSettings}>
                  <Button
                    onClick={handleCreateMobileAppVerificationToken}
                    className={cx('iCal-button')}
                    variant="secondary"
                  >
                    Get the code
                  </Button>
                </WithPermissionControl>
              </p>
            </>
          )}
          <p>
            <Text>* Only iOS is currently supported</Text>
          </p>
        </>
      )}
      {/*<>*/}
      {/*  <GTable*/}
      {/*    title={() => (*/}
      {/*      <div className={cx('header')}>*/}
      {/*        <HorizontalGroup align="flex-end">*/}
      {/*          <Text.Title level={4}>Your devices</Text.Title>*/}
      {/*        </HorizontalGroup>*/}
      {/*      </div>*/}
      {/*    )}*/}
      {/*    rowKey="id"*/}
      {/*    className="api-keys"*/}
      {/*    data={devices}*/}
      {/*    emptyText={devices ? 'No devices connected' : 'Loading...'}*/}
      {/*    columns={columns}*/}
      {/*  />*/}
      {/*</>*/}
    </div>
  );
});

export default MobileAppVerification;
