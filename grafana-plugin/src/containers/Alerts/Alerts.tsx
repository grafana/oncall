import React, { useCallback, useEffect, useState } from 'react';

import { Alert, useStyles2 } from '@grafana/ui';
import { sanitize } from 'dompurify';
import { observer } from 'mobx-react';

import { PluginLink } from 'components/PluginLink/PluginLink';
import { getSlackMessage } from 'containers/DefaultPageLayout/DefaultPageLayout.helpers';
import { SlackError } from 'containers/DefaultPageLayout/DefaultPageLayout.types';
import { getIfChatOpsConnected } from 'containers/DefaultPageLayout/helper';
import { UserHelper } from 'models/user/user.helpers';
import { isTopNavbar } from 'plugin/GrafanaPluginRootPage.helpers';
import { AppFeature } from 'state/features';
import { useStore } from 'state/useStore';
import { LocationHelper } from 'utils/LocationHelper';
import { isUserActionAllowed, UserActions } from 'utils/authorization/authorization';
import { useForceUpdate, useQueryParams } from 'utils/hooks';
import { getItem, setItem } from 'utils/localStorage';

import plugin from '../../../package.json'; // eslint-disable-line
import { GrafanaTheme2 } from '@grafana/data';
import { css, cx } from '@emotion/css';

enum AlertID {
  CONNECTIVITY_WARNING = 'Connectivity Warning',
  USER_GOOGLE_OAUTH2_TOKEN_MISSING_SCOPES = 'User Google OAuth2 token is missing scopes',
}

export const Alerts = observer(() => {
  const queryParams = useQueryParams();
  const [showSlackInstallAlert, setShowSlackInstallAlert] = useState<SlackError | undefined>();
  const styles = useStyles2(getStyles);

  const forceUpdate = useForceUpdate();

  const handleCloseInstallSlackAlert = useCallback(() => {
    setShowSlackInstallAlert(undefined);
  }, []);

  useEffect(() => {
    if (queryParams.get('slack_error')) {
      setShowSlackInstallAlert(queryParams.get('slack_error') as SlackError);

      LocationHelper.update({ slack_error: undefined }, 'partial');
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
    userStore: { currentUser, currentUserPk },
    organizationStore: { currentOrganization },
  } = store;

  const versionMismatchLocalStorageId = `version_mismatch_${store.backendVersion}_${plugin?.version}`;
  const isChatOpsConnected = getIfChatOpsConnected(currentUser);
  const isPhoneVerified = currentUser?.cloud_connection_status === 3 || currentUser?.verified_phone_number;

  const isDefaultNotificationsSet = currentUser?.notification_chain_verbal.default;
  const isImportantNotificationsSet = currentUser?.notification_chain_verbal.important;

  if (
    !showSlackInstallAlert &&
    !showCurrentUserGoogleOAuth2TokenIsMissingScopes() &&
    !showBannerTeam() &&
    !showMismatchWarning() &&
    !showChannelWarnings()
  ) {
    return null;
  }
  return (
    <div className={cx(styles.alertsContainer, { [styles.alertsContainerLegacy]: !isTopNavbar() })}>
      {showSlackInstallAlert && (
        <Alert
          className={styles.alert}
          onRemove={handleCloseInstallSlackAlert}
          severity="error"
          title="Slack integration error"
        >
          {getSlackMessage(showSlackInstallAlert, currentOrganization, store.hasFeature(AppFeature.LiveSettings))}
        </Alert>
      )}
      {showCurrentUserGoogleOAuth2TokenIsMissingScopes() && (
        <Alert
          className={styles.alert}
          severity="warning"
          title="User Google OAuth2 token is missing scopes"
          onRemove={getRemoveAlertHandler(AlertID.USER_GOOGLE_OAUTH2_TOKEN_MISSING_SCOPES)}
        >
          Your Google OAuth2 token is missing some required permissions (you may have forgotten to check the necessary
          checkboxes when connecting your Google account). To rectify this, please grant Grafana OnCall these
          permissions by clicking{' '}
          <a onClick={UserHelper.handleConnectGoogle} className={cx('instructions-link')}>
            here
          </a>{' '}
          and re-connecting your Google account.
        </Alert>
      )}
      {showBannerTeam() && (
        <Alert
          className={styles.alert}
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
          className={styles.alert}
          severity="warning"
          title={'Version mismatch!'}
          onRemove={getRemoveAlertHandler(versionMismatchLocalStorageId)}
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
            className={styles.instructionsLink}
          >
            the update instructions
          </a>
          .
        </Alert>
      )}
      {showChannelWarnings() && (
        <Alert
          onRemove={getRemoveAlertHandler(AlertID.CONNECTIVITY_WARNING)}
          className={styles.alert}
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
      !getItem(versionMismatchLocalStorageId)
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

  /**
   * tbh we don't really need the `currentUserPk` reference here...
   * the only reason why it's here is to appease mobx. Without this reference, the `@computed` property
   * on `UserStore.currentUser` doesn't recalculate and will just be stuck on returning `undefined`..
   *
   * If we dereference `currentUserPk` here, even if we don't use it.. things just seem to work
   * (what is this `mobx` wizardry?)
   *
   * Seems to be related to this https://stackoverflow.com/questions/77724466/mobx-computed-not-updating
   */
  function showCurrentUserGoogleOAuth2TokenIsMissingScopes(): boolean {
    return Boolean(
      currentUserPk &&
        currentUser &&
        currentUser.has_google_oauth2_connected &&
        currentUser.google_oauth2_token_is_missing_scopes &&
        !getItem(AlertID.USER_GOOGLE_OAUTH2_TOKEN_MISSING_SCOPES)
    );
  }
});

const getStyles = (theme: GrafanaTheme2) => {
  return {
    alertsContainer: css`
      display: flex;
      flex-direction: column;
      margin-bottom: 10px;
      gap: 10px;

      '&:empty': {
        display: none;
      }
    `,

    alert: css`
      margin: 0;
    `,

    instructionsLink: css`
      color: ${theme.colors.primary.text};
    `,

    alertsContainerLegacy: css`
      paddingtop: '10px';

      @media (max-width: 768px) {
        padding-top: 50px;
      }
    `,
  };
};
