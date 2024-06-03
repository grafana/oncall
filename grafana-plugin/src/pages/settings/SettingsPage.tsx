import React from 'react';

import { css } from '@emotion/css';
import { AppRootProps } from '@grafana/data';
import { Tab, TabsBar, useStyles2 } from '@grafana/ui';
import { observer } from 'mobx-react';

import { ChatOpsPage } from 'pages/settings/tabs/ChatOps/ChatOps';
import { MainSettings } from 'pages/settings/tabs/MainSettings/MainSettings';
import { isTopNavbar } from 'plugin/GrafanaPluginRootPage.helpers';
import { AppFeature } from 'state/features';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import { LocationHelper } from 'utils/LocationHelper';
import { isUserActionAllowed, UserActions } from 'utils/authorization/authorization';

import { SettingsPageTab } from './SettingsPage.types';
import { CloudPage } from './tabs/Cloud/CloudPage';
import LiveSettingsPage from './tabs/LiveSettings/LiveSettingsPage';
import { TeamsSettings } from './tabs/TeamsSettings/TeamsSettings';

interface SettingsPageProps extends AppRootProps, WithStoreProps {}
interface SettingsPageState {
  activeTab: string;
}

@observer
class Settings extends React.Component<SettingsPageProps, SettingsPageState> {
  constructor(props: SettingsPageProps) {
    super(props);

    const tab = LocationHelper.getQueryParam('tab');

    this.state = {
      activeTab: tab || SettingsPageTab.MainSettings.key,
    };
  }

  render() {
    return <div>{this.renderContent()}</div>;
  }

  renderContent() {
    const { activeTab } = this.state;
    const { store } = this.props;

    const onTabChange = (tab: string) => {
      this.setState({ activeTab: tab });
      LocationHelper.update({ tab }, 'partial');
    };

    const hasLiveSettings = store.hasFeature(AppFeature.LiveSettings);
    const hasCloudPage = store.hasFeature(AppFeature.CloudConnection);
    const showCloudPage = hasCloudPage && isUserActionAllowed(UserActions.OtherSettingsWrite);
    const showLiveSettings = hasLiveSettings && isUserActionAllowed(UserActions.OtherSettingsRead);

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
            <Tab
              key={SettingsPageTab.TeamsSettings.key}
              onChangeTab={() => onTabChange(SettingsPageTab.TeamsSettings.key)}
              active={activeTab === SettingsPageTab.TeamsSettings.key}
              label={SettingsPageTab.TeamsSettings.value}
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
  const styles = useStyles2(getStyles);

  return (
    <div className={styles.tabsContent}>
      {activeTab === SettingsPageTab.MainSettings.key && (
        <div>
          <MainSettings />
        </div>
      )}
      {activeTab === SettingsPageTab.TeamsSettings.key && (
        <div>
          <TeamsSettings />
        </div>
      )}
      {activeTab === SettingsPageTab.ChatOps.key && (
        <div>
          <ChatOpsPage />
        </div>
      )}
      {activeTab === SettingsPageTab.EnvVariables.key && (
        <div>
          <LiveSettingsPage />
        </div>
      )}
      {activeTab === SettingsPageTab.Cloud.key && (
        <div>
          <CloudPage />
        </div>
      )}
    </div>
  );
};

const getStyles = () => {
  return {
    tabsContent: css`
      padding-top: 24px;
    `,
  };
};

export const SettingsPage = withMobXProviderContext(Settings);
