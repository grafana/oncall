import React, { useEffect, useState, useCallback } from 'react';

import { Modal } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import { useMediaQuery } from 'react-responsive';

import { Tabs, TabsContent } from 'containers/UserSettings/parts';
import { User as UserType } from 'models/user/user.types';
import { AppFeature } from 'state/features';
import { useStore } from 'state/useStore';

import { UserSettingsTab } from './UserSettings.types';

import styles from './UserSettings.module.css';

const cx = cn.bind(styles);

const TABS_BREAKPOINT = 1224;

interface UserFormProps {
  onHide: () => void;
  id: UserType['pk'] | 'new';
  onCreate?: (data: UserType) => void;
  onUpdate?: () => void;
  tab?: UserSettingsTab;
}

const UserSettings = observer((props: UserFormProps) => {
  const { id, onHide, tab = UserSettingsTab.UserInfo } = props;

  const store = useStore();
  const { userStore, teamStore } = store;

  const storeUser = userStore.items[id];

  const isCurrent = id === store.userStore.currentUserPk;

  const [activeTab, setActiveTab] = useState<UserSettingsTab>(tab);

  const isDesktopOrLaptop = useMediaQuery({
    query: `(min-width: ${TABS_BREAKPOINT}px)`,
  });

  useEffect(() => {
    if (isDesktopOrLaptop && activeTab === UserSettingsTab.NotificationSettings) {
      setActiveTab(UserSettingsTab.UserInfo);
    }
  }, [isDesktopOrLaptop]);

  const getTabClickHandler = useCallback((tab: UserSettingsTab) => {
    return () => {
      onTabChange(tab);
    };
  }, []);

  const onTabChange = useCallback((tab: UserSettingsTab) => {
    setActiveTab(tab);
  }, []);

  const isModalWide = activeTab === UserSettingsTab.UserInfo && isDesktopOrLaptop;

  const [showNotificationSettingsTab, showSlackConnectionTab, showTelegramConnectionTab, showMobileAppVerificationTab] =
    [
      !isDesktopOrLaptop,
      isCurrent && teamStore.currentTeam?.slack_team_identity && !storeUser.slack_user_identity,
      isCurrent && !storeUser.telegram_configuration,
      store.hasFeature(AppFeature.MobileApp),
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
