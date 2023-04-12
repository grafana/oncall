import React, { useCallback, useEffect, useState } from 'react';

import { Alert } from '@grafana/ui';
import cn from 'classnames/bind';
import { sanitize } from 'dompurify';

import PluginLink from 'components/PluginLink/PluginLink';
import { getSlackMessage } from 'containers/DefaultPageLayout/DefaultPageLayout.helpers';
import { SlackError } from 'containers/DefaultPageLayout/DefaultPageLayout.types';
import { getIfChatOpsConnected } from 'containers/DefaultPageLayout/helper';
import { isTopNavbar } from 'plugin/GrafanaPluginRootPage.helpers';
import { AppFeature } from 'state/features';
import { useStore } from 'state/useStore';
import LocationHelper from 'utils/LocationHelper';
import { isUserActionAllowed, UserActions } from 'utils/authorization';
import { useForceUpdate, useQueryParams } from 'utils/hooks';
import { getItem, setItem } from 'utils/localStorage';

import styles from './Alerts.module.scss';

import plugin from '../../../package.json'; // eslint-disable-line

const cx = cn.bind(styles);

enum AlertID {
  CONNECTIVITY_WARNING = 'Connectivity Warning',
}

export default function Alerts() {
  const queryParams = useQueryParams();
  const [showSlackInstallAlert, setShowSlackInstallAlert] = useState<SlackError | undefined>();

  const forceUpdate = useForceUpdate();

  const handleCloseInstallSlackAlert = useCallback(() => {
    setShowSlackInstallAlert(undefined);
  }, []);

  useEffect(() => {
    if (queryParams.get('slack_error')) {
      setShowSlackInstallAlert(queryParams.get('slack_error') as SlackError);

      LocationHelper.update({ slack_error: undefined }, 'replace');
    }
  }, []);

  const getRemoveAlertHandler = useCallback((id: string) => {
    return () => {
      setItem(id, true);

      forceUpdate();
    };
  }, []);

  const store = useStore();

  const { userStore, teamStore } = store;

  const { currentTeam } = teamStore;
  const { currentUser } = userStore;

  const isChatOpsConnected = getIfChatOpsConnected(currentUser);
  const isPhoneVerified = currentUser?.cloud_connection_status === 3 || currentUser?.verified_phone_number;

  return (
    <div className={cx('alerts-container', { 'alerts-container--legacy': !isTopNavbar() })}>
      {showSlackInstallAlert && (
        <Alert
          className={cx('alert')}
          onRemove={handleCloseInstallSlackAlert}
          severity="warning"
          title="Slack integration warning"
        >
          {getSlackMessage(
            showSlackInstallAlert,
            store.teamStore.currentTeam,
            store.hasFeature(AppFeature.LiveSettings)
          )}
        </Alert>
      )}
      {currentTeam?.banner.title != null && !getItem(currentTeam?.banner.title) && (
        <Alert
          className={cx('alert')}
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
      {store.isOpenSource() &&
        store.backendVersion &&
        plugin?.version &&
        store.backendVersion !== plugin?.version &&
        !getItem(`version_mismatch_${store.backendVersion}_${plugin?.version}`) && (
          <Alert
            className={cx('alert')}
            severity="warning"
            title={'Version mismatch!'}
            onRemove={getRemoveAlertHandler(`version_mismatch_${store.backendVersion}_${plugin?.version}`)}
          >
            Please make sure you have the same versions of the Grafana OnCall plugin and the Grafana OnCall engine,
            otherwise there could be issues with your Grafana OnCall installation!
            <br />
            {`Current plugin version: ${plugin.version}, current engine version: ${store.backendVersion}`}
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
          isUserActionAllowed(UserActions.UserSettingsWrite) &&
          (!isPhoneVerified || !isChatOpsConnected) &&
          !getItem(AlertID.CONNECTIVITY_WARNING)
      ) && (
        <Alert
          onRemove={getRemoveAlertHandler(AlertID.CONNECTIVITY_WARNING)}
          className={cx('alert')}
          severity="warning"
          title="Connectivity Warning"
        >
          {
            <>
              {!isChatOpsConnected && (
                <>Communication channels are not connected. Configure at least one channel to receive notifications.</>
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
  );
}
