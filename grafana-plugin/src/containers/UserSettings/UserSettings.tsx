import React, { useEffect, useState, useCallback } from 'react';

import { HorizontalGroup, Modal } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import { useMediaQuery } from 'react-responsive';

import Avatar from 'components/Avatar/Avatar';
import { Tabs, TabsContent } from 'containers/UserSettings/parts';
import { User as UserType } from 'models/user/user.types';
import { AppFeature } from 'state/features';
import { useStore } from 'state/useStore';
import { BREAKPOINT_TABS } from 'utils/consts';

import { UserSettingsTab } from './UserSettings.types';

import styles from './UserSettings.module.css';

const cx = cn.bind(styles);

interface UserFormProps {
  onHide: () => void;
  id: UserType['pk'] | 'new';
  onCreate?: (data: UserType) => void;
  onUpdate?: () => void;
  tab?: UserSettingsTab;
}

const UserSettings = observer(({ id, onHide, tab = UserSettingsTab.UserInfo }: UserFormProps) => {
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

  const [showNotificationSettingsTab, showSlackConnectionTab, showTelegramConnectionTab, showMobileAppConnectionTab] = [
    !isDesktopOrLaptop,
    isCurrent && organizationStore.currentOrganization?.slack_team_identity && !storeUser.slack_user_identity,
    isCurrent && store.hasFeature(AppFeature.Telegram) && !storeUser.telegram_configuration,
    isCurrent,
  ];

  const title = (
    <HorizontalGroup>
      <Avatar className={cx('user-avatar')} size="large" src={storeUser.avatar} /> <h2>{storeUser.username}</h2>
    </HorizontalGroup>
  );

  return (
    <>
      <Modal title={title} className={cx('modal', 'modal-wide')} isOpen closeOnEscape={false} onDismiss={onHide}>
        <div className={cx('root')}>
          <Tabs
            onTabChange={onTabChange}
            activeTab={activeTab}
            showNotificationSettingsTab={showNotificationSettingsTab}
            showSlackConnectionTab={showSlackConnectionTab}
            showTelegramConnectionTab={showTelegramConnectionTab}
            showMobileAppConnectionTab={showMobileAppConnectionTab}
          />
          <TabsContent id={id} activeTab={activeTab} onTabChange={onTabChange} isDesktopOrLaptop={isDesktopOrLaptop} />
        </div>
      </Modal>
    </>
  );
});

export default UserSettings;
