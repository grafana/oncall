import plugin from '../../../package.json'; // eslint-disable-line
import React, { FC, useEffect, useState, useCallback } from 'react';

import { AppRootProps } from '@grafana/data';
import { getLocationSrv } from '@grafana/runtime';
import { Alert } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import PluginLink from 'components/PluginLink/PluginLink';
import { getIfChatOpsConnected } from 'containers/DefaultPageLayout/helper';
import { useStore } from 'state/useStore';
import { UserAction } from 'state/userAction';
import { GRAFANA_LICENSE_OSS } from 'utils/consts';
import { useForceUpdate } from 'utils/hooks';
import { getItem, setItem } from 'utils/localStorage';
import sanitize from 'utils/sanitize';

import { getSlackMessage } from './DefaultPageLayout.helpers';
import { SlackError } from './DefaultPageLayout.types';

import styles from './DefaultPageLayout.module.css';

const cx = cn.bind(styles);

interface DefaultPageLayoutProps extends AppRootProps {
  children?: any;
}

enum AlertID {
  CONNECTIVITY_WARNING = 'Connectivity Warning',
}

const DefaultPageLayout: FC<DefaultPageLayoutProps> = observer(({ children, query }) => {
  const {
    userStore: { currentUser },
    teamStore: { currentTeam },
    backendLicense,
    backendVersion,
    isUserActionAllowed,
  } = useStore();

  const [showSlackInstallAlert, setShowSlackInstallAlert] = useState<SlackError | undefined>();
  const forceUpdate = useForceUpdate();

  const handleCloseInstallSlackAlert = useCallback(() => {
    setShowSlackInstallAlert(undefined);
  }, []);

  useEffect(() => {
    if (query.slack_error) {
      setShowSlackInstallAlert(query.slack_error);
      getLocationSrv().update({ partial: true, query: { slack_error: undefined }, replace: true });
    }
  }, []);

  const getRemoveAlertHandler = useCallback((id: string) => {
    return () => {
      setItem(id, true);
      forceUpdate();
    };
  }, []);

  const isChatOpsConnected = getIfChatOpsConnected(currentUser);
  const isPhoneVerified = currentUser?.cloud_connection_status === 3 || currentUser?.verified_phone_number;

  return (
    <div className={cx('root')}>
      <div className={styles.alerts_horizontal}>
        {showSlackInstallAlert && (
          <Alert
            className={styles.alert}
            onRemove={handleCloseInstallSlackAlert}
            severity="warning"
            // @ts-ignore
            title="Slack integration warning"
          >
            {getSlackMessage(showSlackInstallAlert, currentTeam)}
          </Alert>
        )}
        {currentTeam?.banner.title != null && !getItem(currentTeam?.banner.title) && (
          <Alert
            className={styles.alert}
            severity="success"
            title={currentTeam.banner.title}
            onRemove={getRemoveAlertHandler(currentTeam?.banner.title)}
          >
            <div
              dangerouslySetInnerHTML={{
                __html: sanitize(currentTeam?.banner.body),
              }}
            />
          </Alert>
        )}
        {backendLicense === GRAFANA_LICENSE_OSS &&
          backendVersion &&
          plugin?.version &&
          backendVersion !== plugin?.version &&
          !getItem(`version_mismatch_${backendVersion}_${plugin?.version}`) && (
            <Alert
              className={styles.alert}
              severity="warning"
              title={'Version mismatch!'}
              onRemove={getRemoveAlertHandler(`version_mismatch_${backendVersion}_${plugin?.version}`)}
            >
              Please make sure you have the same versions of the Grafana OnCall plugin and the Grafana OnCall engine,
              otherwise there could be issues with your Grafana OnCall installation!
              <br />
              {`Current plugin version: ${plugin.version}, current engine version: ${backendVersion}`}
              <br />
              Please see{' '}
              <a
                href={'https://grafana.com/docs/oncall/latest/open-source/#update-grafana-oncall-oss'}
                target="_blank"
                rel="noreferrer"
                className={cx('instructions-link')}
              >
                the update instructions
              </a>
              .
            </Alert>
          )}
        {Boolean(
          currentTeam &&
            currentUser &&
            isUserActionAllowed(UserAction.UpdateOwnSettings) &&
            (!isPhoneVerified || !isChatOpsConnected) &&
            !getItem(AlertID.CONNECTIVITY_WARNING)
        ) && (
          <Alert
            onRemove={getRemoveAlertHandler(AlertID.CONNECTIVITY_WARNING)}
            className={styles.alert}
            severity="warning"
            // @ts-ignore
            title="Connectivity Warning"
          >
            {
              <>
                {!isChatOpsConnected && (
                  <>
                    Communication channels are not connected. Configure at least one channel to receive notifications.
                  </>
                )}
                {!isPhoneVerified && (
                  <>
                    Your phone number is not verified. You can change your configuration in{' '}
                    <PluginLink query={{ page: 'users', id: 'me' }}>User settings</PluginLink>
                  </>
                )}
              </>
            }
          </Alert>
        )}
      </div>
      {children}
    </div>
  );
});

export default DefaultPageLayout;
