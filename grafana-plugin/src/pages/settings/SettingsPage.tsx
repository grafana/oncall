import React from 'react';

import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import styles from './SettingsPage.module.css';
import { pages } from 'pages';
import { Tab, TabsBar } from '@grafana/ui';
import { SettingsPageTab } from './SettingsPage.types';
import ChatOpsPage from 'pages/settings/tabs/ChatOps/ChatOps';
import { withMobXProviderContext } from 'state/withStore';
import MainSettings from 'pages/settings/tabs/MainSettings/MainSettings';
import { PluginPage } from 'PluginPage';
import LiveSettingsPage from './tabs/LiveSettings/LiveSettingsPage';
import CloudPage from './tabs/Cloud/CloudPage';

const cx = cn.bind(styles);

interface SettingsPageProps {}
interface SettingsPageState {
  activeTab: string;
}

@observer
class SettingsPage extends React.Component<SettingsPageProps, SettingsPageState> {
  state: SettingsPageState = {
    activeTab: SettingsPageTab.MainSettings.key, // should read from route instead
  };

  render() {
    const { activeTab } = this.state;

    const onTabChange = (tab: string) => {
      this.setState({ activeTab: tab });
    };

    return (
      <PluginPage pageNav={this.getMatchingPageNav()}>
        <div className={cx('root')}>
          <TabsBar>
            <Tab
              key={SettingsPageTab.MainSettings.key}
              onChangeTab={() => onTabChange(SettingsPageTab.MainSettings.key)}
              active={activeTab === SettingsPageTab.MainSettings.key}
              label={SettingsPageTab.MainSettings.value}
            />
            <Tab
              key={SettingsPageTab.ChatOps.key}
              onChangeTab={() => onTabChange(SettingsPageTab.ChatOps.key)}
              active={activeTab === SettingsPageTab.ChatOps.key}
              label={SettingsPageTab.ChatOps.value}
            />
            <Tab
              key={SettingsPageTab.EnvVariables.key}
              onChangeTab={() => onTabChange(SettingsPageTab.EnvVariables.key)}
              active={activeTab === SettingsPageTab.EnvVariables.key}
              label={SettingsPageTab.EnvVariables.value}
            />
            <Tab
              key={SettingsPageTab.Cloud.key}
              onChangeTab={() => onTabChange(SettingsPageTab.Cloud.key)}
              active={activeTab === SettingsPageTab.Cloud.key}
              label={SettingsPageTab.Cloud.value}
            />
          </TabsBar>

          <TabsContent activeTab={activeTab} />
        </div>
      </PluginPage>
    );
  }

  getMatchingPageNav(): { text: string; description: string } {
    const { activeTab } = this.state;

    switch (activeTab) {
      case SettingsPageTab.MainSettings.key:
        return pages['settings'].getPageNav();
      case SettingsPageTab.ChatOps.key:
        return pages['chat-ops'].getPageNav();
      case SettingsPageTab.EnvVariables.key:
        return pages['live-settings'].getPageNav();
      case SettingsPageTab.Cloud.key:
        return pages['cloud'].getPageNav();
      default:
        return undefined;
    }
  }
}

interface TabsContentProps {
  activeTab: string;
}

const TabsContent = (props: TabsContentProps) => {
  const { activeTab } = props;

  return (
    <div className={cx('tabs__content')}>
      {activeTab === SettingsPageTab.MainSettings.key && (
        <div className={cx('tab__page')}>
          <MainSettings />
        </div>
      )}
      {activeTab === SettingsPageTab.ChatOps.key && (
        <div className={cx('tab__page')}>
          <ChatOpsPage />
        </div>
      )}
      {activeTab === SettingsPageTab.EnvVariables.key && (
        <div className={cx('tab__page')}>
          <LiveSettingsPage />
        </div>
      )}
      {activeTab === SettingsPageTab.Cloud.key && (
        <div className={cx('tab__page')}>
          <CloudPage />
        </div>
      )}
    </div>
  );
};

export default withMobXProviderContext(SettingsPage);
