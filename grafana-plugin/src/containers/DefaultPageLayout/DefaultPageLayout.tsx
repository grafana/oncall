import React, { FC, useEffect, useState, useCallback } from 'react';

import { Alert } from '@grafana/ui';
import { PluginPage } from 'PluginPage';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import { AppRootProps } from 'types';

import PluginLink from 'components/PluginLink/PluginLink';
import { getIfChatOpsConnected } from 'containers/DefaultPageLayout/helper';
import { pages } from 'pages';
import { isTopNavbar } from 'plugin/GrafanaPluginRootPage.helpers';
import { AppFeature } from 'state/features';
import { useStore } from 'state/useStore';
import LocationHelper from 'utils/LocationHelper';
import { isUserActionAllowed, UserActions } from 'utils/authorization';
import { DEFAULT_PAGE, GRAFANA_LICENSE_OSS } from 'utils/consts';
import { useForceUpdate } from 'utils/hooks';

import plugin from '../../../package.json'; // eslint-disable-line

import { getItem, setItem } from 'utils/localStorage';
import sanitize from 'utils/sanitize';

import { getSlackMessage } from './DefaultPageLayout.helpers';
import styles from './DefaultPageLayout.module.scss';
import { SlackError } from './DefaultPageLayout.types';

const cx = cn.bind(styles);

interface DefaultPageLayoutProps extends AppRootProps {
  children?: any;
  page: string;
}

enum AlertID {
  CONNECTIVITY_WARNING = 'Connectivity Warning',
}

const DefaultPageLayout: FC<DefaultPageLayoutProps> = observer((props) => {
  const { children, query, page } = props;

  const [showSlackInstallAlert, setShowSlackInstallAlert] = useState<SlackError | undefined>();

  const forceUpdate = useForceUpdate();

  const handleCloseInstallSlackAlert = useCallback(() => {
    setShowSlackInstallAlert(undefined);
  }, []);

  useEffect(() => {
    if (query.slack_error) {
      setShowSlackInstallAlert(query.slack_error);

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

  if (isTopNavbar()) {
    return renderTopNavbar();
  }

  return renderLegacyNavbar();

  function renderTopNavbar(): JSX.Element {
    return (
      <PluginPage page={page} pageNav={pages[page || DEFAULT_PAGE].getPageNav()} renderAlertsFn={renderAlertsFn}>
        <div className={cx('root')}>{children}</div>
      </PluginPage>
    );
  }

  function renderLegacyNavbar(): JSX.Element {
    return (
      <PluginPage page={page}>
        <div className="page-container u-height-100">
          <div className={cx('root', 'navbar-legacy')}>
            {renderAlertsFn()}
            {children}
          </div>
        </div>
      </PluginPage>
    );
  }

  function renderAlertsFn(): JSX.Element {
    return (
      <div className={cx('alerts-container')}>
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
        {store.backendLicense === GRAFANA_LICENSE_OSS &&
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
    );
  }
});

export default DefaultPageLayout;
