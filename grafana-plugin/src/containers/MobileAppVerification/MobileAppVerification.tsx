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
import QRCode from './parts/QRCode/QRCode';

const cx = cn.bind(styles);

type Props = {
  userPk: User['pk'];
};

const INTERVAL_QUEUE_QR = 50000;
const INTERVAL_POLLING = 5000;
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
  const [refreshTimeoutId, setRefreshTimeoutId] = useState<NodeJS.Timeout>(undefined);
  const [isQRBlurry, setIsQRBlurry] = useState<boolean>(false);

  const fetchQRCode = useCallback(
    async (showLoader = true) => {
      if (showLoader) {
        setFetchingQRCode(true);
      }

      try {
        // backend verification code that we receive is a JSON object that has been "stringified"
        const qrCodeContent = await userStore.sendBackendConfirmationCode(userPk, BACKEND);
        setQRCodeValue(qrCodeContent);
      } catch (e) {
        setErrorFetchingQRCode('There was an error fetching your QR code. Please try again.');
      }

      if (showLoader) {
        setFetchingQRCode(false);
      }
    },
    [userPk]
  );

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
    queueRefreshQR();
    pollUserProfile();
  }, [userPk, resetState]);

  useEffect(() => {
    if (!isUserConnected()) {
      queueRefreshQR();
      pollUserProfile();
    }

    // clear on unmount
    return () => {
      if (userTimeoutId) {
        clearTimeout(userTimeoutId);
        clearTimeout(refreshTimeoutId);
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
        <div className={cx('u-width-100', 'u-flex', 'u-flex-center', 'u-position-relative')}>
          <QRCode className={cx({ blurry: isQRBlurry })} value={QRCodeValue} />
          {isQRBlurry && (
            <div className={cx('blurry-loader')}>
              <LoadingPlaceholder text="Regenerating QR code..." />
            </div>
          )}
        </div>
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

  async function queueRefreshQR(): Promise<void> {
    clearTimeout(refreshTimeoutId);
    setRefreshTimeoutId(undefined);

    const user = await userStore.loadUser(userPk);
    if (!isUserConnected(user)) {
      setIsQRBlurry(true);
      await fetchQRCode(false);
      setIsQRBlurry(false);
      setTimeout(() => queueRefreshQR(), INTERVAL_QUEUE_QR);
    }
  }

  async function pollUserProfile(): Promise<void> {
    clearTimeout(userTimeoutId);
    setUserTimeoutId(undefined);

    const user = await userStore.loadUser(userPk);
    if (!isUserConnected(user)) {
      setUserTimeoutId(setTimeout(() => pollUserProfile(), INTERVAL_POLLING));
    } else {
      setMobileAppIsCurrentlyConnected(true);
    }
  }
});

export default MobileAppVerification;
