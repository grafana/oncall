import React, { useCallback, useEffect } from 'react';

import { Tab, TabContent, TabsBar } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import Block from 'components/GBlock/Block';
import MobileAppVerification from 'containers/MobileAppVerification/MobileAppVerification';
import { UserSettingsTab } from 'containers/UserSettings/UserSettings.types';
import { SlackTab } from 'containers/UserSettings/parts/tabs//SlackTab/SlackTab';
import CloudPhoneSettings from 'containers/UserSettings/parts/tabs/CloudPhoneSettings/CloudPhoneSettings';
import { NotificationSettingsTab } from 'containers/UserSettings/parts/tabs/NotificationSettingsTab';
import PhoneVerification from 'containers/UserSettings/parts/tabs/PhoneVerification/PhoneVerification';
import TelegramInfo from 'containers/UserSettings/parts/tabs/TelegramInfo/TelegramInfo';
import { MatrixInfo } from 'containers/UserSettings/parts/tabs/MatrixTab/MatrixTab';
import { UserInfoTab } from 'containers/UserSettings/parts/tabs/UserInfoTab/UserInfoTab';
import { User } from 'models/user/user.types';
import { AppFeature } from 'state/features';
import { useStore } from 'state/useStore';

import styles from 'containers/UserSettings/parts/index.module.css';

const cx = cn.bind(styles);

interface TabsProps {
  activeTab: UserSettingsTab;
  onTabChange: (tab: UserSettingsTab) => void;
  showNotificationSettingsTab: boolean;
  showMobileAppVerificationTab: boolean;
  showSlackConnectionTab: boolean;
  showTelegramConnectionTab: boolean;
  showMatrixConnectionTab: boolean;
}

export const Tabs = (props: TabsProps) => {
  const {
    activeTab,
    onTabChange,
    showNotificationSettingsTab,
    showMobileAppVerificationTab,
    showSlackConnectionTab,
    showTelegramConnectionTab,
    showMatrixConnectionTab,
  } = props;

  const getTabClickHandler = useCallback(
    (tab: UserSettingsTab) => {
      return () => {
        onTabChange(tab);
      };
    },
    [onTabChange]
  );

  return (
    <TabsBar>
      <Tab
        active={activeTab === UserSettingsTab.UserInfo}
        label="User Info"
        key={UserSettingsTab.UserInfo}
        onChangeTab={getTabClickHandler(UserSettingsTab.UserInfo)}
      />
      {showNotificationSettingsTab && (
        <Tab
          active={activeTab === UserSettingsTab.NotificationSettings}
          label="Notification Settings"
          key={UserSettingsTab.NotificationSettings}
          onChangeTab={getTabClickHandler(UserSettingsTab.NotificationSettings)}
        />
      )}
      <Tab
        active={activeTab === UserSettingsTab.PhoneVerification}
        label="Phone Verification"
        key={UserSettingsTab.PhoneVerification}
        onChangeTab={getTabClickHandler(UserSettingsTab.PhoneVerification)}
      />
      {showMobileAppVerificationTab && (
        <Tab
          active={activeTab === UserSettingsTab.MobileAppVerification}
          label="Mobile App Verification"
          key={UserSettingsTab.MobileAppVerification}
          onChangeTab={getTabClickHandler(UserSettingsTab.MobileAppVerification)}
        />
      )}
      {showSlackConnectionTab && (
        <Tab
          active={activeTab === UserSettingsTab.SlackInfo}
          label="Slack Connection"
          key={UserSettingsTab.SlackInfo}
          onChangeTab={getTabClickHandler(UserSettingsTab.SlackInfo)}
        />
      )}
      {showTelegramConnectionTab && (
        <Tab
          active={activeTab === UserSettingsTab.TelegramInfo}
          label="Telegram Connection"
          key={UserSettingsTab.TelegramInfo}
          onChangeTab={getTabClickHandler(UserSettingsTab.TelegramInfo)}
        />
      )}
      {showMatrixConnectionTab && (
        <Tab
          active={activeTab === UserSettingsTab.MatrixInfo}
          label="Matrix Connection"
          key={UserSettingsTab.MatrixInfo}
          onChangeTab={getTabClickHandler(UserSettingsTab.MatrixInfo)}
        />
      )}
    </TabsBar>
  );
};

interface TabsContentProps {
  id: User['pk'];
  activeTab: UserSettingsTab;
  onTabChange: (tab: UserSettingsTab) => void;
  isDesktopOrLaptop: boolean;
}

export const TabsContent = observer((props: TabsContentProps) => {
  const { id, activeTab, onTabChange, isDesktopOrLaptop } = props;
  useEffect(() => {
    store.updateFeatures();
  }, []);

  const store = useStore();
  const { userStore } = store;

  const storeUser = userStore.items[id];

  return (
    <TabContent className={cx('content')}>
      {activeTab === UserSettingsTab.UserInfo &&
        (isDesktopOrLaptop ? (
          <div className={cx('columns')}>
            <Block shadowed bordered style={{ width: '30%' }} className={cx('col', 'left')}>
              <UserInfoTab id={id} onTabChange={onTabChange} />
            </Block>
            <Block shadowed bordered style={{ width: '70%' }} className={cx('col', 'right')}>
              <NotificationSettingsTab id={id} />
            </Block>
          </div>
        ) : (
          <UserInfoTab id={id} onTabChange={onTabChange} />
        ))}
      {activeTab === UserSettingsTab.NotificationSettings && <NotificationSettingsTab id={id} />}
      {activeTab === UserSettingsTab.PhoneVerification &&
        (store.hasFeature(AppFeature.CloudNotifications) ? (
          <CloudPhoneSettings userPk={id} />
        ) : (
          <PhoneVerification userPk={id} />
        ))}
      {activeTab === UserSettingsTab.MobileAppVerification && (
        <MobileAppVerification userPk={id} phone={storeUser.unverified_phone_number || '+'} />
      )}
      {activeTab === UserSettingsTab.SlackInfo && <SlackTab />}
      {activeTab === UserSettingsTab.TelegramInfo && <TelegramInfo />}
      {activeTab === UserSettingsTab.MatrixInfo && <MatrixInfo userPk={id} />}
    </TabContent>
  );
});
