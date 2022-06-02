import React, { FC, useEffect, useState, useCallback } from 'react';

import { AppRootProps } from '@grafana/data';
import { getLocationSrv } from '@grafana/runtime';
import { Alert, Button } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import PluginLink from 'components/PluginLink/PluginLink';
import { useStore } from 'state/useStore';
import { UserAction } from 'state/userAction';
import { useForceUpdate } from 'utils/hooks';
import { getItem, setItem } from 'utils/localStorage';
import sanitize from 'utils/sanitize';

import { getSlackMessage } from './DefaultPageLayout.helpers';
import { SlackError } from './DefaultPageLayout.types';

import styles from './DefaultPageLayout.module.css';

const cx = cn.bind(styles);

interface DefaultPageLayoutProps extends AppRootProps {}

enum AlertID {
  CONNECTIVITY_WARNING = 'Connectivity Warning',
}

const DefaultPageLayout: FC<DefaultPageLayoutProps> = observer((props) => {
  const { children, query } = props;

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

  const store = useStore();

  const { userStore, teamStore } = store;

  const { currentTeam } = teamStore;
  const { currentUser } = userStore;

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
            {getSlackMessage(showSlackInstallAlert, store.teamStore.currentTeam)}
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
        {currentTeam?.limits.show_limits_warning && !getItem(currentTeam.limits.warning_text) && (
          <Alert
            className={styles.alert}
            severity="warning"
            title={currentTeam?.limits.warning_text}
            onRemove={getRemoveAlertHandler(currentTeam?.limits.warning_text)}
          />
        )}
        {Boolean(
          currentTeam &&
            currentUser &&
            store.isUserActionAllowed(UserAction.UpdateOwnSettings) &&
            (!currentUser.verified_phone_number || !currentUser.slack_user_identity) &&
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
                {!currentTeam.slack_team_identity && (
                  <>
                    Slack Integration is not installed. Please fix it in{' '}
                    <PluginLink query={{ page: 'chat-ops' }}>Slack Settings</PluginLink>
                    {'. '}
                  </>
                )}
                {!currentUser.verified_phone_number && 'Your phone number is not verified. '}
                {currentTeam.slack_team_identity &&
                  !currentUser.slack_user_identity &&
                  'Your slack account is not connected. '}
                You can change your configuration in{' '}
                <PluginLink query={{ page: 'users', id: 'me' }}>User settings</PluginLink>
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
