import React, { useCallback, useEffect, useRef, useState } from 'react';

import { css, cx } from '@emotion/css';
import { Button, Icon, LoadingPlaceholder, Stack, useStyles2 } from '@grafana/ui';
import { UserActions } from 'helpers/authorization/authorization';
import { IS_CURRENT_ENV_CLOUD, StackSize } from 'helpers/consts';
import { isMobile, openNotification, openWarningNotification, openErrorNotification } from 'helpers/helpers';
import { useInitializePlugin } from 'helpers/hooks';
import { observer } from 'mobx-react';

import qrCodeImage from 'assets/img/qr-code.png';
import { Block } from 'components/GBlock/Block';
import { PluginLink } from 'components/PluginLink/PluginLink';
import { RenderConditionally } from 'components/RenderConditionally/RenderConditionally';
import { Text } from 'components/Text/Text';
import { PluginInitializer } from 'containers/PluginInitializer/PluginInitializer';
import { WithPermissionControlDisplay } from 'containers/WithPermissionControl/WithPermissionControlDisplay';
import { UserHelper } from 'models/user/user.helpers';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { AppFeature } from 'state/features';
import { RootStore, rootStore as store } from 'state/rootStore';

import { getMobileAppConnectionStyles } from './MobileAppConnection.styles';
import { DisconnectButton } from './parts/DisconnectButton/DisconnectButton';
import { DownloadIcons } from './parts/DownloadIcons/DownloadIcons';
import { LinkLoginButton } from './parts/LinkLoginButton/LinkLoginButton';
import { QRCode } from './parts/QRCode/QRCode';

type Props = {
  userPk?: ApiSchemas['User']['pk'];
  store?: RootStore;
};

const INTERVAL_MIN_THROTTLING = 500;
/**
 * 290_000 = 4 minutes and 50 seconds
 * QR code token has a TTL of 5 minutes
 * This means we will fetch a new token just before the current one expires
 */
const INTERVAL_QUEUE_QR = 290_000;
const INTERVAL_POLLING = 5000;
const BACKEND = 'MOBILE_APP';

export const MobileAppConnection = observer(({ userPk }: Props) => {
  const { userStore, cloudStore } = store;

  const [basicDataLoaded, setBasicDataLoaded] = useState(false);

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
  const [isAttemptingTestNotification, setIsAttemptingTestNotification] = useState(false);
  const isCurrentUser = userPk === undefined || userStore.currentUserPk === userPk;

  const styles = useStyles2(getMobileAppConnectionStyles);

  useEffect(() => {
    isMounted.current = true;

    (async () => {
      if (!isUserConnected()) {
        triggerTimeouts();
      } else {
        setMobileAppIsCurrentlyConnected(true);
      }

      setBasicDataLoaded(true);
    })();

    // clear on unmount
    return () => {
      isMounted.current = false;
      clearTimeouts();
    };
  }, []);

  const fetchQRCode = useCallback(
    async (showLoader = true) => {
      if (!userPk) {
        return;
      }

      if (showLoader) {
        setFetchingQRCode(true);
      }

      try {
        // backend verification code that we receive is a JSON object that has been "stringified"
        const qrCodeContent = await UserHelper.fetchBackendConfirmationCode(userPk, BACKEND);
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
    if (!userPk) {
      return;
    }
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
    if (!mobileAppIsCurrentlyConnected) {
      fetchQRCode();
    }
  }, [mobileAppIsCurrentlyConnected, userPk]);

  // Show link to cloud page for OSS instances with no cloud connection
  if (
    !IS_CURRENT_ENV_CLOUD &&
    store.hasFeature(AppFeature.CloudConnection) &&
    !cloudStore.cloudConnectionStatus.cloud_connection_status
  ) {
    return renderConnectToCloud();
  }

  let content: React.ReactNode = null;
  const QRCodeDataParsed = QRCodeValue && getParsedQRCodeValue();

  if (fetchingQRCode || disconnectingMobileApp || !userPk || !basicDataLoaded) {
    content = <LoadingPlaceholder text="Loading..." />;
  } else if (errorFetchingQRCode || errorDisconnectingMobileApp) {
    content = <Text type="primary">{errorFetchingQRCode || errorDisconnectingMobileApp}</Text>;
  } else if (mobileAppIsCurrentlyConnected) {
    content = (
      <Stack direction="column" gap={StackSize.lg}>
        <Text strong type="primary">
          App connected <Icon name="check-circle" size="md" className={styles.icon} />
        </Text>
        <Text type="primary">
          You can only sync one application to your account. To setup a new device, please disconnect the currently
          connected device first.
        </Text>
        <div className={styles.disconnectContainer}>
          <img src={qrCodeImage} className={styles.disconnectQRCode} />
          <DisconnectButton onClick={disconnectMobileApp} />
        </div>
      </Stack>
    );
  } else if (QRCodeValue) {
    content = (
      <Stack direction="column" gap={StackSize.lg}>
        <Text type="primary" strong>
          Sign in via QR Code
        </Text>
        <Text type="primary">
          Open the Grafana OnCall mobile application and scan this code to sync it with your account.
        </Text>
        <div
          className={css`
            width: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
            position: relative;
          `}
        >
          <QRCode className={cx({ [styles.qrCode]: true, [styles.blurry]: isQRBlurry })} value={QRCodeValue} />
          {isQRBlurry && <QRLoading />}
        </div>
        {!IS_CURRENT_ENV_CLOUD && QRCodeDataParsed && (
          <Text type="secondary">
            Server URL embedded in this QR:
            <br />
            <a href={QRCodeDataParsed.oncall_api_url}>
              <Text type="link">{QRCodeDataParsed.oncall_api_url}</Text>
            </a>
          </Text>
        )}
      </Stack>
    );
  }

  return (
    <>
      <h3>Mobile App Connection</h3>
      <Stack direction="column">
        <div className={styles.container}>
          {QRCodeDataParsed && isMobile && (
            <Block shadowed bordered withBackground className={styles.containerBox}>
              <LinkLoginButton baseUrl={QRCodeDataParsed.oncall_api_url} token={QRCodeDataParsed.token} />
            </Block>
          )}
          <Block shadowed bordered withBackground className={styles.containerBox}>
            {content}
          </Block>
          <Block shadowed bordered withBackground className={styles.containerBox}>
            <DownloadIcons />
          </Block>
        </div>
        {mobileAppIsCurrentlyConnected && isCurrentUser && !disconnectingMobileApp && (
          <div className={styles.notificationButtons}>
            <Stack gap={StackSize.md} justifyContent={'flex-end'}>
              <Button
                variant="secondary"
                onClick={() => onSendTestNotification()}
                disabled={isAttemptingTestNotification}
              >
                Send Test Push
              </Button>
              <Button
                variant="secondary"
                onClick={() => onSendTestNotification(true)}
                disabled={isAttemptingTestNotification}
              >
                Send Test Push Important
              </Button>
            </Stack>
          </div>
        )}
      </Stack>
    </>
  );

  function renderConnectToCloud() {
    return (
      <WithPermissionControlDisplay userAction={UserActions.UserSettingsWrite}>
        <Stack direction="column" gap={StackSize.lg}>
          <Text type="secondary">Please connect Grafana Cloud OnCall to use the mobile app</Text>
          <WithPermissionControlDisplay
            userAction={UserActions.OtherSettingsWrite}
            message="You do not have permission to perform this action. Ask an admin to connect Grafana Cloud OnCall or upgrade your
            permissions."
          >
            <PluginLink query={{ page: 'cloud' }}>
              <Button variant="secondary" icon="external-link-alt">
                Connect Grafana Cloud OnCall
              </Button>
            </PluginLink>
          </WithPermissionControlDisplay>
        </Stack>
      </WithPermissionControlDisplay>
    );
  }

  async function onSendTestNotification(isCritical = false) {
    if (!userPk) {
      return;
    }
    setIsAttemptingTestNotification(true);

    try {
      await UserHelper.sendTestPushNotification(userPk, isCritical);
      openNotification(isCritical ? 'Push Important Notification has been sent' : 'Push Notification has been sent');
    } catch (ex) {
      if (ex.response?.status === 429) {
        openWarningNotification('Too much attempts, try again later');
      } else {
        openErrorNotification('There was an error sending the notification');
      }
    } finally {
      setIsAttemptingTestNotification(false);
    }
  }

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

  function isUserConnected(user?: ApiSchemas['User']): boolean {
    return !!(user || userStore.currentUser)?.messaging_backends[BACKEND]?.connected;
  }

  async function queueRefreshQR(): Promise<void> {
    if (!isMounted.current || !userPk) {
      return;
    }

    clearTimeout(refreshTimeoutId);
    setRefreshTimeoutId(undefined);

    const user = await userStore.fetchItemById({ userPk });
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
    if (!isMounted.current || !userPk) {
      return;
    }

    clearTimeout(userTimeoutId);
    setUserTimeoutId(undefined);

    const user = await userStore.fetchItemById({ userPk });
    if (!isUserConnected(user)) {
      setUserTimeoutId(setTimeout(pollUserProfile, INTERVAL_POLLING));
    } else {
      setMobileAppIsCurrentlyConnected(true);
    }
  }
});

function QRLoading() {
  const styles = useStyles2(getMobileAppConnectionStyles);

  return (
    <div className={styles.qrLoader}>
      <Text type="primary" className={styles.qrLoaderText}>
        Regenerating QR code...
      </Text>
      <LoadingPlaceholder text="Loading..." />
    </div>
  );
}

export const MobileAppConnectionWrapper: React.FC<{}> = observer(() => {
  const { userStore } = store;
  const { isConnected } = useInitializePlugin();

  useEffect(() => {
    if (isConnected) {
      loadData();
    }
  }, [isConnected]);

  const loadData = async () => {
    if (!store.isBasicDataLoaded) {
      await store.loadBasicData();
    }

    if (!userStore.currentUserPk) {
      await userStore.loadCurrentUser();
    }
  };

  return (
    <PluginInitializer>
      <RenderConditionally
        shouldRender={Boolean(store.isBasicDataLoaded && userStore.currentUserPk)}
        render={() => (
          <div data-testid="mobile-app-connection">
            <MobileAppConnection userPk={userStore.currentUserPk} />
          </div>
        )}
        backupChildren={<LoadingPlaceholder text="Loading..." />}
      />
    </PluginInitializer>
  );
});
