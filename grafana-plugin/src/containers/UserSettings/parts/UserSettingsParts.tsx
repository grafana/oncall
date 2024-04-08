import React, { useCallback, useEffect } from 'react';

import { Tab, TabContent, TabsBar } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import { Block } from 'components/GBlock/Block';
import { MobileAppConnection } from 'containers/MobileAppConnection/MobileAppConnection';
import { MobileAppConnectionTab } from 'containers/MobileAppConnection/MobileAppConnectionTab';
import { UserSettingsTab } from 'containers/UserSettings/UserSettings.types';
import { SlackTab } from 'containers/UserSettings/parts/tabs//SlackTab/SlackTab';
import { CloudPhoneSettings } from 'containers/UserSettings/parts/tabs/CloudPhoneSettings/CloudPhoneSettings';
import { GoogleCalendar } from 'containers/UserSettings/parts/tabs/GoogleCalendar/GoogleCalendar';
import { MSTeamsInfo } from 'containers/UserSettings/parts/tabs/MSTeamsInfo/MSTeamsInfo';
import { NotificationSettingsTab } from 'containers/UserSettings/parts/tabs/NotificationSettingsTab';
import { PhoneVerification } from 'containers/UserSettings/parts/tabs/PhoneVerification/PhoneVerification';
import { TelegramInfo } from 'containers/UserSettings/parts/tabs/TelegramInfo/TelegramInfo';
import { UserInfoTab } from 'containers/UserSettings/parts/tabs/UserInfoTab/UserInfoTab';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { AppFeature } from 'state/features';
import { useStore } from 'state/useStore';
import { isUseProfileExtensionPointEnabled } from 'utils/utils';

import styles from 'containers/UserSettings/parts/UserSettingsParts.module.css';

const cx = cn.bind(styles);

interface TabsProps {
  activeTab: UserSettingsTab;
  onTabChange: (tab: UserSettingsTab) => void;
  showNotificationSettingsTab: boolean;
  showMobileAppConnectionTab: boolean;
  showGoogleCalendarTab: boolean;
  showSlackConnectionTab: boolean;
  showTelegramConnectionTab: boolean;
  showMsTeamsConnectionTab: boolean;
}

export const Tabs = ({
  activeTab,
  onTabChange,
  showNotificationSettingsTab,
  showGoogleCalendarTab,
  showMobileAppConnectionTab,
  showSlackConnectionTab,
  showTelegramConnectionTab,
  showMsTeamsConnectionTab,
}: TabsProps) => {
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
        data-testid="tab-user-info"
      />
      {showNotificationSettingsTab && (
        <Tab
          active={activeTab === UserSettingsTab.NotificationSettings}
          label="Notification Settings"
          key={UserSettingsTab.NotificationSettings}
          onChangeTab={getTabClickHandler(UserSettingsTab.NotificationSettings)}
          data-testid="tab-notification-settings"
        />
      )}
      {showGoogleCalendarTab && (
        <Tab
          active={activeTab === UserSettingsTab.GoogleCalendar}
          label="Google Calendar"
          key={UserSettingsTab.GoogleCalendar}
          onChangeTab={getTabClickHandler(UserSettingsTab.GoogleCalendar)}
          data-testid="google-calendar-tab"
        />
      )}
      <Tab
        active={activeTab === UserSettingsTab.PhoneVerification}
        label="Phone Verification"
        key={UserSettingsTab.PhoneVerification}
        onChangeTab={getTabClickHandler(UserSettingsTab.PhoneVerification)}
        data-testid="tab-phone-verification"
      />
      {showMobileAppConnectionTab && (
        <Tab
          active={activeTab === UserSettingsTab.MobileAppConnection}
          label="Mobile App Connection"
          key={UserSettingsTab.MobileAppConnection}
          onChangeTab={getTabClickHandler(UserSettingsTab.MobileAppConnection)}
          data-testid="tab-mobile-app"
        />
      )}
      {showSlackConnectionTab && (
        <Tab
          active={activeTab === UserSettingsTab.SlackInfo}
          label="Slack Connection"
          key={UserSettingsTab.SlackInfo}
          onChangeTab={getTabClickHandler(UserSettingsTab.SlackInfo)}
          data-testid="tab-slack"
        />
      )}
      {showTelegramConnectionTab && (
        <Tab
          active={activeTab === UserSettingsTab.TelegramInfo}
          label="Telegram Connection"
          key={UserSettingsTab.TelegramInfo}
          onChangeTab={getTabClickHandler(UserSettingsTab.TelegramInfo)}
          data-testid="tab-telegram"
        />
      )}
      {showMsTeamsConnectionTab && (
        <Tab
          active={activeTab === UserSettingsTab.MSTeamsInfo}
          label="Ms Teams Connection"
          key={UserSettingsTab.MSTeamsInfo}
          onChangeTab={getTabClickHandler(UserSettingsTab.MSTeamsInfo)}
          data-testid="tab-msteams"
        />
      )}
    </TabsBar>
  );
};

interface TabsContentProps {
  id: ApiSchemas['User']['pk'];
  activeTab: UserSettingsTab;
  onTabChange: (tab: UserSettingsTab) => void;
  isDesktopOrLaptop: boolean;
}

export const TabsContent = observer(({ id, activeTab, onTabChange, isDesktopOrLaptop }: TabsContentProps) => {
  const store = useStore();

  useEffect(() => {
    store.updateFeatures();
  }, []);

  return (
    <TabContent className={cx('content')}>
      {activeTab === UserSettingsTab.UserInfo &&
        (isDesktopOrLaptop ? (
          <div className={cx('columns')}>
            <Block shadowed bordered style={{ width: '40%' }} className={cx('col', 'left')}>
              <UserInfoTab id={id} onTabChange={onTabChange} />
            </Block>
            <Block shadowed bordered style={{ width: '60%' }} className={cx('col', 'right')}>
              <NotificationSettingsTab id={id} />
            </Block>
          </div>
        ) : (
          <UserInfoTab id={id} onTabChange={onTabChange} />
        ))}
      {activeTab === UserSettingsTab.NotificationSettings && <NotificationSettingsTab id={id} />}
      {activeTab === UserSettingsTab.GoogleCalendar && <GoogleCalendar id={id} />}
      {activeTab === UserSettingsTab.PhoneVerification &&
        (store.hasFeature(AppFeature.CloudNotifications) ? (
          <CloudPhoneSettings userPk={id} />
        ) : (
          <PhoneVerification userPk={id} />
        ))}
      {activeTab === UserSettingsTab.MobileAppConnection && renderMobileTab()}
      {activeTab === UserSettingsTab.SlackInfo && <SlackTab />}
      {activeTab === UserSettingsTab.TelegramInfo && <TelegramInfo />}
      {activeTab === UserSettingsTab.MSTeamsInfo && <MSTeamsInfo />}
    </TabContent>
  );

  function renderMobileTab() {
    if (!isUseProfileExtensionPointEnabled()) {
      return <MobileAppConnection userPk={id} />;
    }

    return <MobileAppConnectionTab userPk={id} />;
  }
});
