import React, { useEffect, useState, useCallback } from 'react';

import { Alert, Modal, Stack } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import { useMediaQuery } from 'react-responsive';

import { Avatar } from 'components/Avatar/Avatar';
import { Tabs, TabsContent } from 'containers/UserSettings/parts/UserSettingsParts';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { AppFeature } from 'state/features';
import { useStore } from 'state/useStore';
import { LocationHelper } from 'utils/LocationHelper';
import { BREAKPOINT_TABS } from 'utils/consts';
import { useQueryParams } from 'utils/hooks';

import { UserSettingsTab } from './UserSettings.types';

import styles from './UserSettings.module.css';

const cx = cn.bind(styles);

enum GoogleError {
  MISSING_GRANTED_SCOPE = 'missing_granted_scope',
}

interface UserFormProps {
  onHide: () => void;
  id: ApiSchemas['User']['pk'] | 'new';
  onCreate?: (data: ApiSchemas['User']) => void;
  onUpdate?: () => void;
  tab?: UserSettingsTab;
}

function getGoogleMessage(googleError: GoogleError) {
  if (googleError === GoogleError.MISSING_GRANTED_SCOPE) {
    return (
      <>
        Couldn't connect your Google account. You did not grant Grafana OnCall the necessary permissions. Please retry
        and be sure to check any checkboxes which grant Grafana OnCall read access to your calendar events.
      </>
    );
  }

  return <>Couldn't connect your Google account.</>;
}

const UserAlerts: React.FC = () => {
  const queryParams = useQueryParams();
  const [showGoogleConnectAlert, setShowGoogleConnectAlert] = useState<GoogleError | undefined>();

  const handleCloseGoogleAlert = useCallback(() => {
    setShowGoogleConnectAlert(undefined);
  }, []);

  useEffect(() => {
    if (queryParams.get('google_error')) {
      setShowGoogleConnectAlert(queryParams.get('google_error') as GoogleError);

      LocationHelper.update({ google_error: undefined }, 'partial');
    }
  }, []);

  if (!showGoogleConnectAlert) {
    return null;
  }

  return (
    <div className={cx('alerts-container')}>
      <Alert
        className={cx('alert')}
        onRemove={handleCloseGoogleAlert}
        severity="error"
        title="Google integration error"
      >
        {getGoogleMessage(showGoogleConnectAlert)}
      </Alert>
    </div>
  );
};

export const UserSettings = observer(({ id, onHide, tab = UserSettingsTab.UserInfo }: UserFormProps) => {
  const store = useStore();
  const { userStore, organizationStore } = store;

  const storeUser = userStore.items[id];
  const isCurrent = id === store.userStore.currentUserPk;

  const [activeTab, setActiveTab] = useState<UserSettingsTab>(tab);

  const isDesktopOrLaptop = useMediaQuery({
    query: `(min-width: ${BREAKPOINT_TABS}px)`,
  });

  useEffect(() => {
    if (isDesktopOrLaptop && activeTab === UserSettingsTab.NotificationSettings) {
      setActiveTab(UserSettingsTab.UserInfo);
    }
  }, [isDesktopOrLaptop, activeTab]);

  const onTabChange = useCallback((tab: UserSettingsTab) => {
    setActiveTab(tab);
  }, []);

  const [
    showNotificationSettingsTab,
    showSlackConnectionTab,
    showTelegramConnectionTab,
    showMobileAppConnectionTab,
    showMsTeamsConnectionTab,
    showGoogleCalendarTab,
  ] = [
    !isDesktopOrLaptop,
    isCurrent && organizationStore.currentOrganization?.slack_team_identity && !storeUser.slack_user_identity,
    isCurrent && store.hasFeature(AppFeature.Telegram) && !storeUser.telegram_configuration,
    isCurrent,
    store.hasFeature(AppFeature.MsTeams) && !storeUser.messaging_backends.MSTEAMS,
    isCurrent && store.hasFeature(AppFeature.GoogleOauth2),
  ];

  const title = (
    <Stack>
      <Avatar className={cx('user-avatar')} size="large" src={storeUser.avatar} /> <h2>{storeUser.username}</h2>
    </Stack>
  );

  return (
    <>
      <Modal title={title} className={cx('modal', 'modal-wide')} isOpen closeOnEscape={false} onDismiss={onHide}>
        <UserAlerts />
        <div className={cx('root')}>
          <Tabs
            onTabChange={onTabChange}
            activeTab={activeTab}
            showNotificationSettingsTab={showNotificationSettingsTab}
            showSlackConnectionTab={showSlackConnectionTab}
            showTelegramConnectionTab={showTelegramConnectionTab}
            showMobileAppConnectionTab={showMobileAppConnectionTab}
            showMsTeamsConnectionTab={showMsTeamsConnectionTab}
            showGoogleCalendarTab={showGoogleCalendarTab}
          />
          <TabsContent id={id} activeTab={activeTab} onTabChange={onTabChange} isDesktopOrLaptop={isDesktopOrLaptop} />
        </div>
      </Modal>
    </>
  );
});
