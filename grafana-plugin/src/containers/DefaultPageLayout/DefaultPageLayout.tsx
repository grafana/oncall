import React, { FC, useEffect, useState, useCallback } from 'react';

import { Alert } from '@grafana/ui';
import { PluginPage } from 'PluginPage';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import { AppRootProps } from 'types';

import PluginLink from 'components/PluginLink/PluginLink';
import { getIfChatOpsConnected } from 'containers/DefaultPageLayout/helper';
import { pages } from 'pages';
import { AppFeature } from 'state/features';
import { useStore } from 'state/useStore';

import plugin from '../../../package.json'; // eslint-disable-line

import LocationHelper from 'utils/LocationHelper';
import { isUserActionAllowed, UserActions } from 'utils/authorization';
import { DEFAULT_PAGE, GRAFANA_LICENSE_OSS } from 'utils/consts';
import { useForceUpdate, useQueryParams } from 'utils/hooks';
import { getItem, setItem } from 'utils/localStorage';
import sanitize from 'utils/sanitize';

import { getSlackMessage } from './DefaultPageLayout.helpers';
import styles from './DefaultPageLayout.module.scss';
import { SlackError } from './DefaultPageLayout.types';

const cx = cn.bind(styles);

interface DefaultPageLayoutProps extends AppRootProps {
  children?: any;
}

enum AlertID {
  CONNECTIVITY_WARNING = 'Connectivity Warning',
}

const DefaultPageLayout: FC<DefaultPageLayoutProps> = observer((props) => {
  const { children, query } = props;
  const queryParams = useQueryParams();

  const [showSlackInstallAlert, setShowSlackInstallAlert] = useState<SlackError | undefined>();

  const forceUpdate = useForceUpdate();
  const page = queryParams.get('page') || DEFAULT_PAGE;

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

  return (
    <PluginPage
      pageNav={pages[page].getPageNav()}
      renderAlertsFn={() => (
        <div className={cx('alerts_horizontal')}>
          {showSlackInstallAlert && (
            <Alert
              className={styles.alert}
              onRemove={handleCloseInstallSlackAlert}
              severity="warning"
              // @ts-ignore
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
          {store.backendLicense === GRAFANA_LICENSE_OSS &&
            store.backendVersion &&
            plugin?.version &&
            store.backendVersion !== plugin?.version &&
            !getItem(`version_mismatch_${store.backendVersion}_${plugin?.version}`) && (
              <Alert
                className={styles.alert}
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
      )}
    >
      <div className={cx('root')}>{children}</div>
    </PluginPage>
  );
});

export default DefaultPageLayout;
