import React, { useCallback, useEffect, useState } from 'react';

import { HorizontalGroup, LoadingPlaceholder, VerticalGroup } from '@grafana/ui';
import { observer } from 'mobx-react';

import Block from 'components/GBlock/Block';
import Text from 'components/Text/Text';
import { User } from 'models/user/user.types';
import { useStore } from 'state/useStore';

import DisconnectButton from './parts/DisconnectButton';
import DownloadIcons from './parts/DownloadIcons';
import QRCode from './parts/QRCode';

type Props = {
  userPk: User['pk'];
};

const BACKEND = 'MOBILE_APP';

const MobileAppVerification = observer(({ userPk }: Props) => {
  const { userStore } = useStore();

  const [mobileAppIsCurrentlyConnected, setMobileAppIsCurrentlyConnected] = useState<boolean>(
    userStore.currentUser.messaging_backends[BACKEND]?.connected === true
  );

  const [fetchingQRCode, setFetchingQRCode] = useState<boolean>(!mobileAppIsCurrentlyConnected);
  const [QRCodeValue, setQRCodeValue] = useState<string>(null);
  const [errorFetchingQRCode, setErrorFetchingQRCode] = useState<string>(null);

  const [disconnectingMobileApp, setDisconnectingMobileApp] = useState<boolean>(false);
  const [errorDisconnectingMobileApp, setErrorDisconnectingMobileApp] = useState<string>(null);

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
  }, [userPk, resetState]);

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
        <Text type="primary">Your mobile app is currently connected. Click below to disconnect.</Text>
        <DisconnectButton onClick={disconnectMobileApp} />
      </VerticalGroup>
    );
  } else if (QRCodeValue) {
    content = (
      <VerticalGroup spacing="lg">
        <Text type="primary">Sign In</Text>
        <Text type="primary">Open Grafana IRM mobile application and scan this code to sync it with your account.</Text>
        <QRCode value={QRCodeValue} />
        <Text type="primary" className="u-break-word">
          <strong>Note:</strong> the QR code is only valid for one minute. If you have issues connecting your mobile
          app, try refreshing this page to generate a new code.
        </Text>
      </VerticalGroup>
    );
  }

  return (
    <HorizontalGroup align={'normal'}>
      <Block bordered withBackground>
        {content}
      </Block>
      <Block bordered withBackground>
        <DownloadIcons />
      </Block>
    </HorizontalGroup>
  );
});

export default MobileAppVerification;
