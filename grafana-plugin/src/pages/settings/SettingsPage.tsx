import React from 'react';

import { Tab, TabsBar } from '@grafana/ui';
import { PluginPage } from 'PluginPage';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import ChatOpsPage from 'pages/settings/tabs/ChatOps/ChatOps';
import MainSettings from 'pages/settings/tabs/MainSettings/MainSettings';
import { isTopNavbar } from 'plugin/GrafanaPluginRootPage.helpers';
import { AppFeature } from 'state/features';
import { RootBaseStore } from 'state/rootBaseStore';
import { withMobXProviderContext } from 'state/withStore';
import { UserActions } from 'utils/authorization';

import { SettingsPageTab } from './SettingsPage.types';
import CloudPage from './tabs/Cloud/CloudPage';
import LiveSettingsPage from './tabs/LiveSettings/LiveSettingsPage';

import styles from './SettingsPage.module.css';

const cx = cn.bind(styles);

interface SettingsPageProps {
  store: RootBaseStore;
}
interface SettingsPageState {
  activeTab: string;
}

@observer
class SettingsPage extends React.Component<SettingsPageProps, SettingsPageState> {
  state: SettingsPageState = {
    activeTab: SettingsPageTab.MainSettings.key, // should read from route instead
  };

  render() {
    return (
      <PluginPage pageNav={this.getMatchingPageNav()}>
        <div className={cx('root')}>{this.renderContent()}</div>
      </PluginPage>
    );
  }

  renderContent() {
    const { activeTab } = this.state;
    const { store } = this.props;

    const onTabChange = (tab: string) => {
      this.setState({ activeTab: tab });
    };

    const hasLiveSettings = store.hasFeature(AppFeature.LiveSettings);
    const hasCloudPage = store.hasFeature(AppFeature.CloudConnection);
    const showCloudPage = hasCloudPage && store.isUserActionAllowed(UserActions.OtherSettingsWrite);
    const showLiveSettings = hasLiveSettings && store.isUserActionAllowed(UserActions.OtherSettingsRead);

    if (isTopNavbar()) {
      return (
        <>
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
            {showLiveSettings && (
              <Tab
                key={SettingsPageTab.EnvVariables.key}
                onChangeTab={() => onTabChange(SettingsPageTab.EnvVariables.key)}
                active={activeTab === SettingsPageTab.EnvVariables.key}
                label={SettingsPageTab.EnvVariables.value}
              />
            )}
            {showCloudPage && (
              <Tab
                key={SettingsPageTab.Cloud.key}
                onChangeTab={() => onTabChange(SettingsPageTab.Cloud.key)}
                active={activeTab === SettingsPageTab.Cloud.key}
                label={SettingsPageTab.Cloud.value}
              />
            )}
          </TabsBar>

          <TabsContent activeTab={activeTab} />
        </>
      );
    }

    return <MainSettings />;
  }

  getMatchingPageNav() {
    return {
      parentItem: {
        text: getTabText(this.state.activeTab),
      },
      text: '',
      hideFromBreadcrumbs: true,
    };

    function getTabText(activeTab: string) {
      let result: string;
      Object.keys(SettingsPageTab).forEach((tab) => {
        if (activeTab === SettingsPageTab[tab].key) {
          result = SettingsPageTab[tab].value;
        }
      });

      return result;
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
