import React, { useCallback, useEffect, useRef, useState } from 'react';

import { Button, Icon, LoadingPlaceholder, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import qrCodeImage from 'assets/img/qr-code.png';
import Block from 'components/GBlock/Block';
import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import { User } from 'models/user/user.types';
import { AppFeature } from 'state/features';
import { useStore } from 'state/useStore';
import { isUserActionAllowed, UserActions } from 'utils/authorization';
import { GRAFANA_LICENSE_OSS } from 'utils/consts';

import styles from './MobileAppConnection.module.scss';
import DisconnectButton from './parts/DisconnectButton/DisconnectButton';
import DownloadIcons from './parts/DownloadIcons';
import QRCode from './parts/QRCode/QRCode';

const cx = cn.bind(styles);

type Props = {
  userPk: User['pk'];
};

const INTERVAL_MIN_THROTTLING = 500;
const INTERVAL_QUEUE_QR = process.env.MOBILE_APP_QR_INTERVAL_QUEUE
  ? parseInt(process.env.MOBILE_APP_QR_INTERVAL_QUEUE, 10)
  : 50000;
const INTERVAL_POLLING = 5000;
const BACKEND = 'MOBILE_APP';

const MobileAppConnection = observer(({ userPk }: Props) => {
  const store = useStore();
  const { userStore, cloudStore } = store;

  // Show link to cloud page for OSS instances with no cloud connection
  if (store.hasFeature(AppFeature.CloudConnection) && !cloudStore.cloudConnectionStatus.cloud_connection_status) {
    return (
      <VerticalGroup spacing="lg">
        <Text type="secondary">Please connect Cloud OnCall to use the mobile app</Text>
        {isUserActionAllowed(UserActions.OtherSettingsWrite) ? (
          <PluginLink query={{ page: 'cloud' }}>
            <Button variant="secondary" icon="external-link-alt">
              Connect Cloud OnCall
            </Button>
          </PluginLink>
        ) : (
          <Text type="secondary">
            You do not have permission to perform this action. Ask an admin to connect Cloud OnCall or upgrade your
            permissions.
          </Text>
        )}
      </VerticalGroup>
    );
  }

  const isMounted = useRef(false);
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
    clearTimeouts();
    triggerTimeouts();
  }, [userPk, resetState]);

  useEffect(() => {
    isMounted.current = true;

    if (!isUserConnected()) {
      triggerTimeouts();
    }

    // clear on unmount
    return () => {
      isMounted.current = false;
      clearTimeouts();
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
    const QRCodeDataParsed = getParsedQRCodeValue();

    content = (
      <VerticalGroup spacing="lg">
        <Text type="primary" strong>
          Sign In
        </Text>
        <Text type="primary">Open Grafana IRM mobile application and scan this code to sync it with your account.</Text>
        <div className={cx('u-width-100', 'u-flex', 'u-flex-center', 'u-position-relative')}>
          <QRCode className={cx({ 'qr-code': true, blurry: isQRBlurry })} value={QRCodeValue} />
          {isQRBlurry && <QRLoading />}
        </div>
        {store.backendLicense === GRAFANA_LICENSE_OSS && QRCodeDataParsed && (
          <Text type="secondary">
            Server URL embedded in this QR:
            <br />
            <a href={QRCodeDataParsed.oncall_api_url}>
              <Text type="link">{QRCodeDataParsed.oncall_api_url}</Text>
            </a>
          </Text>
        )}
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

  function getParsedQRCodeValue() {
    try {
      return JSON.parse(QRCodeValue);
    } catch (ex) {
      return undefined;
    }
  }

  function clearTimeouts(): void {
    clearTimeout(userTimeoutId);
    clearTimeout(refreshTimeoutId);
  }

  function triggerTimeouts(): void {
    setTimeout(queueRefreshQR, INTERVAL_QUEUE_QR);
    setTimeout(pollUserProfile, INTERVAL_POLLING);
  }

  function isUserConnected(user?: User): boolean {
    return !!(user || userStore.currentUser).messaging_backends[BACKEND]?.connected;
  }

  async function queueRefreshQR(): Promise<void> {
    if (!isMounted.current) {
      return;
    }

    clearTimeout(refreshTimeoutId);
    setRefreshTimeoutId(undefined);

    const user = await userStore.loadUser(userPk);
    if (!isUserConnected(user)) {
      let didCallThrottleWithNoEffect = false;
      let isRequestDone = false;

      const throttle = () => {
        if (!isMounted.current) {
          return;
        }
        if (!isRequestDone) {
          didCallThrottleWithNoEffect = true;
          return;
        }

        setIsQRBlurry(false);
        setTimeout(queueRefreshQR, INTERVAL_QUEUE_QR);
      };

      setTimeout(throttle, INTERVAL_MIN_THROTTLING);
      setIsQRBlurry(true);

      await fetchQRCode(false);

      isRequestDone = true;
      if (didCallThrottleWithNoEffect) {
        throttle();
      }
    }
  }

  async function pollUserProfile(): Promise<void> {
    if (!isMounted.current) {
      return;
    }

    clearTimeout(userTimeoutId);
    setUserTimeoutId(undefined);

    const user = await userStore.loadUser(userPk);
    if (!isUserConnected(user)) {
      setUserTimeoutId(setTimeout(pollUserProfile, INTERVAL_POLLING));
    } else {
      setMobileAppIsCurrentlyConnected(true);
    }
  }
});

function QRLoading() {
  return (
    <div className={cx('qr-loader')}>
      <Text type="primary" className={cx('qr-loader__text')}>
        Regenerating QR code...
      </Text>
      <LoadingPlaceholder />
    </div>
  );
}

export default MobileAppConnection;
