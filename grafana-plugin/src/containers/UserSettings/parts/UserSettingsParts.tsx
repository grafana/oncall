import React, { useCallback, useEffect } from 'react';

import { css } from '@emotion/css';
import { Tab, TabContent, TabsBar, useStyles2 } from '@grafana/ui';
import { isUseProfileExtensionPointEnabled } from 'helpers/helpers';
import { observer } from 'mobx-react';

import { Block } from 'components/GBlock/Block';
import { MobileAppConnection } from 'containers/MobileAppConnection/MobileAppConnection';
import { MobileAppConnectionTab } from 'containers/MobileAppConnection/MobileAppConnectionTab';
import { UserSettingsTab } from 'containers/UserSettings/UserSettings.types';
import { SlackTab } from 'containers/UserSettings/parts/tabs//SlackTab/SlackTab';
import { CloudPhoneSettings } from 'containers/UserSettings/parts/tabs/CloudPhoneSettings/CloudPhoneSettings';
import { GoogleCalendar } from 'containers/UserSettings/parts/tabs/GoogleCalendar/GoogleCalendar';
import { MSTeamsInfo } from 'containers/UserSettings/parts/tabs/MSTeamsInfo/MSTeamsInfo';
import { MattermostInfo } from 'containers/UserSettings/parts/tabs/MattermostInfo/MattermostInfo';
import { NotificationSettingsTab } from 'containers/UserSettings/parts/tabs/NotificationSettingsTab';
import { PersonalWebhookInfo } from 'containers/UserSettings/parts/tabs/PersonalWebhookInfo/PersonalWebhookInfo';
import { PhoneVerification } from 'containers/UserSettings/parts/tabs/PhoneVerification/PhoneVerification';
import { TelegramInfo } from 'containers/UserSettings/parts/tabs/TelegramInfo/TelegramInfo';
import { UserInfoTab } from 'containers/UserSettings/parts/tabs/UserInfoTab/UserInfoTab';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { AppFeature } from 'state/features';
import { useStore } from 'state/useStore';

interface TabsProps {
  activeTab: UserSettingsTab;
  onTabChange: (tab: UserSettingsTab) => void;
  showNotificationSettingsTab: boolean;
  showMobileAppConnectionTab: boolean;
  showGoogleCalendarTab: boolean;
  showSlackConnectionTab: boolean;
  showTelegramConnectionTab: boolean;
  showPersonalWebhookConnectionTab: boolean;
  showMsTeamsConnectionTab: boolean;
  showMattermostConnectionTab: boolean;
}

export const Tabs = ({
  activeTab,
  onTabChange,
  showNotificationSettingsTab,
  showGoogleCalendarTab,
  showMobileAppConnectionTab,
  showSlackConnectionTab,
  showTelegramConnectionTab,
  showPersonalWebhookConnectionTab,
  showMsTeamsConnectionTab,
  showMattermostConnectionTab,
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
        label="User info"
        key={UserSettingsTab.UserInfo}
        onChangeTab={getTabClickHandler(UserSettingsTab.UserInfo)}
        data-testid="tab-user-info"
      />
      {showNotificationSettingsTab && (
        <Tab
          active={activeTab === UserSettingsTab.NotificationSettings}
          label="Notification settings"
          key={UserSettingsTab.NotificationSettings}
          onChangeTab={getTabClickHandler(UserSettingsTab.NotificationSettings)}
          data-testid="tab-notification-settings"
        />
      )}
      {showGoogleCalendarTab && (
        <Tab
          active={activeTab === UserSettingsTab.GoogleCalendar}
          label="Google calendar"
          key={UserSettingsTab.GoogleCalendar}
          onChangeTab={getTabClickHandler(UserSettingsTab.GoogleCalendar)}
          data-testid="google-calendar-tab"
        />
      )}
      <Tab
        active={activeTab === UserSettingsTab.PhoneVerification}
        label="Phone verification"
        key={UserSettingsTab.PhoneVerification}
        onChangeTab={getTabClickHandler(UserSettingsTab.PhoneVerification)}
        data-testid="tab-phone-verification"
      />
      {showMobileAppConnectionTab && (
        <Tab
          active={activeTab === UserSettingsTab.MobileAppConnection}
          label="Mobile app connection"
          key={UserSettingsTab.MobileAppConnection}
          onChangeTab={getTabClickHandler(UserSettingsTab.MobileAppConnection)}
          data-testid="tab-mobile-app"
        />
      )}
      {showSlackConnectionTab && (
        <Tab
          active={activeTab === UserSettingsTab.SlackInfo}
          label="Slack connection"
          key={UserSettingsTab.SlackInfo}
          onChangeTab={getTabClickHandler(UserSettingsTab.SlackInfo)}
          data-testid="tab-slack"
        />
      )}
      {showTelegramConnectionTab && (
        <Tab
          active={activeTab === UserSettingsTab.TelegramInfo}
          label="Telegram connection"
          key={UserSettingsTab.TelegramInfo}
          onChangeTab={getTabClickHandler(UserSettingsTab.TelegramInfo)}
          data-testid="tab-telegram"
        />
      )}
      {showPersonalWebhookConnectionTab && (
        <Tab
          active={activeTab === UserSettingsTab.PersonalWebhookInfo}
          label="Webhook connection"
          key={UserSettingsTab.PersonalWebhookInfo}
          onChangeTab={getTabClickHandler(UserSettingsTab.PersonalWebhookInfo)}
          data-testid="tab-personalwebhook"
        />
      )}
      {showMsTeamsConnectionTab && (
        <Tab
          active={activeTab === UserSettingsTab.MSTeamsInfo}
          label="Ms Teams connection"
          key={UserSettingsTab.MSTeamsInfo}
          onChangeTab={getTabClickHandler(UserSettingsTab.MSTeamsInfo)}
          data-testid="tab-msteams"
        />
      )}
      {showMattermostConnectionTab && (
        <Tab
          active={activeTab === UserSettingsTab.MattermostInfo}
          label="Mattermost Connection"
          key={UserSettingsTab.MattermostInfo}
          onChangeTab={getTabClickHandler(UserSettingsTab.MattermostInfo)}
          data-testid="tab-mattermost"
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
  const styles = useStyles2(getUserSettingsPartsStyles);

  useEffect(() => {
    store.updateFeatures();
  }, []);

  return (
    <TabContent className={styles.content}>
      {activeTab === UserSettingsTab.UserInfo &&
        (isDesktopOrLaptop ? (
          <div className={styles.columns}>
            <Block shadowed bordered style={{ width: '40%' }} className={styles.col}>
              <UserInfoTab id={id} onTabChange={onTabChange} />
            </Block>
            <Block shadowed bordered style={{ width: '60%' }} className={styles.col}>
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
      {activeTab === UserSettingsTab.PersonalWebhookInfo && <PersonalWebhookInfo />}
      {activeTab === UserSettingsTab.MSTeamsInfo && <MSTeamsInfo />}
      {activeTab === UserSettingsTab.MattermostInfo && <MattermostInfo />}
    </TabContent>
  );

  function renderMobileTab() {
    if (!isUseProfileExtensionPointEnabled()) {
      return <MobileAppConnection userPk={id} />;
    }

    return <MobileAppConnectionTab userPk={id} />;
  }
});

export const getUserSettingsPartsStyles = () => {
  return {
    content: css`
      margin-top: 20px;
    `,

    columns: css`
      display: flex;
      flex-direction: row;
    `,

    col: css`
      display: flex;
      flex-direction: column;
    `,

    right: css`
      margin-left: 24px;
      display: flex;
      flex-direction: column;
      justify-content: flex-start;
    `,

    rightCentered: css`
      text-align: center;
      justify-content: center;
    `,

    tagContainer: css`
      display: flex;
      gap: 4px;
      width: 100%;
    `,

    tag: css`
      font-weight: 500;
      font-size: 12px;
      height: 32px;
      line-height: 32px;
      padding: 0 8px;
      width: 120px;
    `,

    tagLeft: css`
      flex-basis: 120px;
    `,

    tagRight: css`
      flex-basis: calc(100% - 120px);
    `,
  };
};
