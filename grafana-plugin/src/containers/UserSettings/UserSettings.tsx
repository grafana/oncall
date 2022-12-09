import React, { useEffect, useState, useCallback } from 'react';

import { Modal } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import { useMediaQuery } from 'react-responsive';

import { Tabs, TabsContent } from 'containers/UserSettings/parts';
import { User as UserType } from 'models/user/user.types';
import { useStore } from 'state/useStore';
import { BREAKPOINT_TABS } from 'utils/consts';

import { UserSettingsTab } from './UserSettings.types';

import styles from './UserSettings.module.css';

const cx = cn.bind(styles);

interface UserFormProps {
  onHide: () => void;
  id: UserType['pk'] | 'new';
  showMobileAppScreen: boolean;
  onCreate?: (data: UserType) => void;
  onUpdate?: () => void;
  tab?: UserSettingsTab;
}

const UserSettings = observer(({ id, showMobileAppScreen, onHide, tab = UserSettingsTab.UserInfo }: UserFormProps) => {
  const store = useStore();
  const { userStore, teamStore } = store;

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

  const isModalWide =
    !isDesktopOrLaptop ||
    activeTab === UserSettingsTab.UserInfo ||
    activeTab === UserSettingsTab.PhoneVerification ||
    activeTab === UserSettingsTab.MobileAppVerification;

  const [showNotificationSettingsTab, showSlackConnectionTab, showTelegramConnectionTab, showMobileAppVerificationTab] =
    [
      !isDesktopOrLaptop,
      isCurrent && teamStore.currentTeam?.slack_team_identity && !storeUser.slack_user_identity,
      isCurrent && !storeUser.telegram_configuration,
      showMobileAppScreen,
    ];

  return (
    <>
      <Modal
        title={`${storeUser.username}`}
        className={cx('modal', { 'modal-wide': isModalWide })}
        isOpen
        closeOnEscape={false}
        onDismiss={onHide}
      >
        <div className={cx('root')}>
          <Tabs
            onTabChange={onTabChange}
            activeTab={activeTab}
            showNotificationSettingsTab={showNotificationSettingsTab}
            showSlackConnectionTab={showSlackConnectionTab}
            showTelegramConnectionTab={showTelegramConnectionTab}
            showMobileAppVerificationTab={showMobileAppVerificationTab}
          />
          <TabsContent id={id} activeTab={activeTab} onTabChange={onTabChange} isDesktopOrLaptop={isDesktopOrLaptop} />
        </div>
      </Modal>
    </>
  );
});

export default UserSettings;
