import React, { useCallback, useEffect, useState } from 'react';

import { Icon, LoadingPlaceholder, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import qrCodeImage from 'assets/img/qr-code.png';
import Block from 'components/GBlock/Block';
import Text from 'components/Text/Text';
import { User } from 'models/user/user.types';
import { useStore } from 'state/useStore';

import styles from './MobileAppVerification.module.scss';
import DisconnectButton from './parts/DisconnectButton/DisconnectButton';
import DownloadIcons from './parts/DownloadIcons';
import QRCode from './parts/QRCode';

const cx = cn.bind(styles);

type Props = {
  userPk: User['pk'];
};

const INTERVAL_MS = 5000;
const BACKEND = 'MOBILE_APP';

const MobileAppVerification = observer(({ userPk }: Props) => {
  const { userStore } = useStore();

  const [mobileAppIsCurrentlyConnected, setMobileAppIsCurrentlyConnected] = useState<boolean>(isUserConnected());

  const [fetchingQRCode, setFetchingQRCode] = useState<boolean>(!mobileAppIsCurrentlyConnected);
  const [QRCodeValue, setQRCodeValue] = useState<string>(null);
  const [errorFetchingQRCode, setErrorFetchingQRCode] = useState<string>(null);

  const [disconnectingMobileApp, setDisconnectingMobileApp] = useState<boolean>(false);
  const [errorDisconnectingMobileApp, setErrorDisconnectingMobileApp] = useState<string>(null);
  const [userTimeoutId, setUserTimeoutId] = useState<NodeJS.Timeout>(undefined);

  const fetchQRCode = useCallback(async () => {
    setFetchingQRCode(true);
    try {
      // backend verification code that we receive is a JSON object that has been "stringified"
      const qrCodeContent = await userStore.sendBackendConfirmationCode(userPk, BACKEND);
      setQRCodeValue(qrCodeContent);
    } catch (e) {
      setErrorFetchingQRCode('There was an error fetching your QR code. Please try again.');
    }
    setFetchingQRCode(false);
  }, [userPk]);

  const resetState = useCallback(() => {
    setErrorDisconnectingMobileApp(null);
    setMobileAppIsCurrentlyConnected(false);
    setQRCodeValue(null);
  }, []);

  const disconnectMobileApp = useCallback(async () => {
    setDisconnectingMobileApp(true);

    try {
      await userStore.unlinkBackend(userPk, BACKEND);
      resetState();
    } catch (e) {
      setErrorDisconnectingMobileApp('There was an error disconnecting your mobile app. Please try again.');
    }

    setDisconnectingMobileApp(false);
    pollUserProfile();
  }, [userPk, resetState]);

  useEffect(() => {
    if (!isUserConnected()) {
      pollUserProfile();
    }

    // clear on unmount
    return () => {
      if (userTimeoutId) {
        clearTimeout(userTimeoutId);
      }
    };
  }, []);

  useEffect(() => {
    if (!mobileAppIsCurrentlyConnected) {
      fetchQRCode();
    }
  }, [mobileAppIsCurrentlyConnected]);

  let content: React.ReactNode = null;

  if (fetchingQRCode || disconnectingMobileApp) {
    content = <LoadingPlaceholder text="Loading..." />;
  } else if (errorFetchingQRCode || errorDisconnectingMobileApp) {
    content = <Text type="primary">{errorFetchingQRCode || errorDisconnectingMobileApp}</Text>;
  } else if (mobileAppIsCurrentlyConnected) {
    content = (
      <VerticalGroup spacing="lg">
        <Text strong type="primary">
          App connected <Icon name="check-circle" size="md" className={cx('icon')} />
        </Text>
        <Text type="primary">
          You can sync one application to your account. To setup new device please disconnect app first.
        </Text>
        <div className={cx('disconnect__container')}>
          <img src={qrCodeImage} className={cx('disconnect__qrCode')} />
          <DisconnectButton onClick={disconnectMobileApp} />
        </div>
      </VerticalGroup>
    );
  } else if (QRCodeValue) {
    content = (
      <VerticalGroup spacing="lg">
        <Text type="primary" strong>
          Sign In
        </Text>
        <Text type="primary">Open Grafana IRM mobile application and scan this code to sync it with your account.</Text>
        <div className="u-width-100 u-flex u-flex-center">
          <QRCode value={QRCodeValue} />
        </div>
        <Text type="primary" className="u-break-word">
          <strong>Note:</strong> the QR code is only valid for one minute. If you have issues connecting your mobile
          app, try refreshing this page to generate a new code.
        </Text>
      </VerticalGroup>
    );
  }

  return (
    <div className={cx('container')}>
      <Block shadowed bordered withBackground className={cx('container__box')}>
        <DownloadIcons />
      </Block>
      <Block shadowed bordered withBackground className={cx('container__box')}>
        {content}
      </Block>
    </div>
  );

  function isUserConnected(user?: User): boolean {
    return !!(user || userStore.currentUser).messaging_backends[BACKEND]?.connected;
  }

  async function pollUserProfile(): Promise<void> {
    clearTimeout(userTimeoutId);
    setUserTimeoutId(undefined);

    const user = await userStore.loadUser(userPk);
    if (!isUserConnected(user)) {
      setUserTimeoutId(setTimeout(() => pollUserProfile(), INTERVAL_MS));
    } else {
      setMobileAppIsCurrentlyConnected(true);
    }
  }
});

export default MobileAppVerification;
