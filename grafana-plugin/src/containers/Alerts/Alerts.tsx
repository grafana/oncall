import React, { useCallback, useEffect, useState } from 'react';

import { Alert } from '@grafana/ui';
import cn from 'classnames/bind';
import { sanitize } from 'dompurify';

import { PluginLink } from 'components/PluginLink/PluginLink';
import { getSlackMessage } from 'containers/DefaultPageLayout/DefaultPageLayout.helpers';
import { SlackError } from 'containers/DefaultPageLayout/DefaultPageLayout.types';
import { getIfChatOpsConnected } from 'containers/DefaultPageLayout/helper';
import { isTopNavbar } from 'plugin/GrafanaPluginRootPage.helpers';
import { AppFeature } from 'state/features';
import { useStore } from 'state/useStore';
import { LocationHelper } from 'utils/LocationHelper';
import { isUserActionAllowed, UserActions } from 'utils/authorization/authorization';
import { useForceUpdate, useQueryParams } from 'utils/hooks';
import { getItem, setItem } from 'utils/localStorage';

import styles from './Alerts.module.scss';

import plugin from '../../../package.json'; // eslint-disable-line

const cx = cn.bind(styles);

enum AlertID {
  CONNECTIVITY_WARNING = 'Connectivity Warning',
}

export const Alerts = function () {
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
  const {
    userStore: { currentUser },
    organizationStore: { currentOrganization },
  } = store;

  const isChatOpsConnected = getIfChatOpsConnected(currentUser);
  const isPhoneVerified = currentUser?.cloud_connection_status === 3 || currentUser?.verified_phone_number;

  const isDefaultNotificationsSet = currentUser?.notification_chain_verbal.default;
  const isImportantNotificationsSet = currentUser?.notification_chain_verbal.important;

  if (!showSlackInstallAlert && !showBannerTeam() && !showMismatchWarning() && !showChannelWarnings()) {
    return null;
  }
  return (
    <div className={cx('alerts-container', { 'alerts-container--legacy': !isTopNavbar() })}>
      {showSlackInstallAlert && (
        <Alert
          className={cx('alert')}
          onRemove={handleCloseInstallSlackAlert}
          severity="error"
          title="Slack integration error"
        >
          {getSlackMessage(showSlackInstallAlert, currentOrganization, store.hasFeature(AppFeature.LiveSettings))}
        </Alert>
      )}
      {showBannerTeam() && (
        <Alert
          className={cx('alert')}
          severity="success"
          title={currentOrganization.banner.title}
          onRemove={getRemoveAlertHandler(currentOrganization?.banner.title)}
        >
          <div
            dangerouslySetInnerHTML={{
              __html: sanitize(currentOrganization?.banner.body),
            }}
          />
        </Alert>
      )}
      {showMismatchWarning() && (
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
      {showChannelWarnings() && (
        <Alert
          onRemove={getRemoveAlertHandler(AlertID.CONNECTIVITY_WARNING)}
          className={cx('alert')}
          severity="warning"
          title="Notification Warning! Possible notification miss."
        >
          {
            <>
              {!isDefaultNotificationsSet && <>Default notification chain is not set. </>}
              {!isImportantNotificationsSet && <>Important notification chain is not set. </>}
              {!isChatOpsConnected && <>No messenger connected for ChatOps. </>}
              {!isPhoneVerified && <>Your phone number is not verified. </>}
              <>
                You can change your configuration in{' '}
                <PluginLink query={{ page: 'users', id: 'me' }}>User profile settings</PluginLink>
              </>
            </>
          }
        </Alert>
      )}
    </div>
  );

  function showBannerTeam(): boolean {
    return Boolean(currentOrganization?.banner?.title) && !getItem(currentOrganization?.banner?.title);
  }

  function showMismatchWarning(): boolean {
    return (
      store.isOpenSource &&
      store.backendVersion &&
      plugin?.version &&
      store.backendVersion !== plugin?.version &&
      !getItem(`version_mismatch_${store.backendVersion}_${plugin?.version}`)
    );
  }

  function showChannelWarnings(): boolean {
    return Boolean(
      currentOrganization &&
        currentUser &&
        isUserActionAllowed(UserActions.UserSettingsWrite) &&
        (!isPhoneVerified || !isChatOpsConnected) &&
        !getItem(AlertID.CONNECTIVITY_WARNING)
    );
  }
};
