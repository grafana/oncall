import React from 'react';

import { css } from '@emotion/css';
import { AppRootProps, GrafanaTheme2 } from '@grafana/data';
import { Alert, Icon, Stack, Themeable2, withTheme2 } from '@grafana/ui';
import { LocationHelper } from 'helpers/LocationHelper';
import { IS_CURRENT_ENV_OSS } from 'helpers/consts';
import { observer } from 'mobx-react';

import { VerticalTabsBar, VerticalTab } from 'components/VerticalTabsBar/VerticalTabsBar';
import { MSTeamsSettings } from 'pages/settings/tabs/ChatOps/tabs/MSTeamsSettings/MSTeamsSettings';
import { MattermostSettings } from 'pages/settings/tabs/ChatOps/tabs/MattermostSettings/MattermostSettings';
import { SlackSettings } from 'pages/settings/tabs/ChatOps/tabs/SlackSettings/SlackSettings';
import { TelegramSettings } from 'pages/settings/tabs/ChatOps/tabs/TelegramSettings/TelegramSettings';
import { AppFeature } from 'state/features';
import { WithStoreProps } from 'state/types';
import { useStore } from 'state/useStore';
import { withMobXProviderContext } from 'state/withStore';

import { handleChatOpsQueryParamError } from './ChatOps.helpers';

export enum ChatOpsTab {
  Slack = 'Slack',
  Telegram = 'Telegram',
  MSTeams = 'MSTeams',
  Mattermost = 'Mattermost',
}
interface ChatOpsProps extends AppRootProps, WithStoreProps, Themeable2 {}
interface ChatOpsState {
  activeTab: ChatOpsTab;
}

@observer
export class _ChatOpsPage extends React.Component<ChatOpsProps, ChatOpsState> {
  state: ChatOpsState = {
    activeTab: ChatOpsTab.Slack,
  };

  componentDidMount() {
    const tab = LocationHelper.getQueryParam('chatOpsTab');

    handleChatOpsQueryParamError();
    this.handleChatopsTabChange(tab || ChatOpsTab.Slack);
  }

  componentWillUnmount() {
    this.handleChatopsTabChange(undefined);
  }

  render() {
    const { activeTab } = this.state;
    const { theme } = this.props;
    const styles = getStyles(theme);

    if (!this.isChatOpsConfigured() && IS_CURRENT_ENV_OSS) {
      return this.renderNoChatOpsBannerInfo();
    }

    return (
      <div className={styles.root}>
        <div className={styles.tabs}>
          <Tabs activeTab={activeTab} onTabChange={(tab: ChatOpsTab) => this.handleChatopsTabChange(tab)} />
        </div>
        <div className={styles.content}>
          <TabsContent activeTab={activeTab} />
        </div>
      </div>
    );
  }

  renderNoChatOpsBannerInfo() {
    const { theme } = this.props;
    const styles = getStyles(theme);

    return (
      <div className={styles.root} data-testid="chatops-banner">
        <Alert severity="warning" title="No ChatOps found">
          ChatOps is disabled because no chat integration is enabled. See{' '}
          <a href="https://grafana.com/docs/oncall/latest/open-source/#telegram-setup" target="_blank" rel="noreferrer">
            Telegram
          </a>{' '}
          and{' '}
          <a href="https://grafana.com/docs/oncall/latest/open-source/#slack-setup" target="_blank" rel="noreferrer">
            Slack
          </a>{' '}
          docs for more information.
        </Alert>
      </div>
    );
  }

  isChatOpsConfigured(): boolean {
    const { store } = this.props;
    return (
      store.hasFeature(AppFeature.Slack) ||
      store.hasFeature(AppFeature.Telegram) ||
      store.hasFeature(AppFeature.MsTeams) ||
      store.hasFeature(AppFeature.Mattermost)
    );
  }

  handleChatopsTabChange(tab: ChatOpsTab) {
    this.setState({ activeTab: tab });
    LocationHelper.update({ chatOpsTab: tab }, 'partial');
  }
}

export const ChatOpsPage = withMobXProviderContext(withTheme2(_ChatOpsPage));

interface TabsProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

const Tabs = (props: TabsProps) => {
  const { activeTab, onTabChange } = props;
  const store = useStore();

  return (
    <VerticalTabsBar activeTab={activeTab} onChange={onTabChange}>
      {store.hasFeature(AppFeature.Slack) && (
        <VerticalTab id={ChatOpsTab.Slack}>
          <Stack>
            <Icon name="slack" />
            Slack
          </Stack>
        </VerticalTab>
      )}

      {store.hasFeature(AppFeature.Telegram) && (
        <VerticalTab id={ChatOpsTab.Telegram}>
          <Stack>
            <Icon name="message" />
            Telegram
          </Stack>
        </VerticalTab>
      )}
      {store.hasFeature(AppFeature.MsTeams) && (
        <VerticalTab id={ChatOpsTab.MSTeams}>
          <Stack>
            <Icon name="microsoft" />
            Microsoft Teams
          </Stack>
        </VerticalTab>
      )}
      {store.hasFeature(AppFeature.Mattermost) && (
        <VerticalTab id={ChatOpsTab.Mattermost}>
          <Stack>
            <Icon name="message" />
            Mattermost
          </Stack>
        </VerticalTab>
      )}
      {store.hasFeature(AppFeature.Mattermost) && (
        <VerticalTab id={ChatOpsTab.Mattermost}>
          <HorizontalGroup>
            <Icon name="message" />
            Mattermost
          </HorizontalGroup>
        </VerticalTab>
      )}
    </VerticalTabsBar>
  );
};

interface TabsContentProps {
  activeTab: string;
}

const TabsContent = (props: TabsContentProps) => {
  const { activeTab } = props;
  const store = useStore();

  return (
    <>
      {store.hasFeature(AppFeature.Slack) && activeTab === ChatOpsTab.Slack && <SlackSettings />}
      {store.hasFeature(AppFeature.Telegram) && activeTab === ChatOpsTab.Telegram && <TelegramSettings />}
      {store.hasFeature(AppFeature.MsTeams) && activeTab === ChatOpsTab.MSTeams && <MSTeamsSettings />}
      {store.hasFeature(AppFeature.Mattermost) && activeTab === ChatOpsTab.Mattermost && <MattermostSettings />}
    </>
  );
};

const getStyles = (theme: GrafanaTheme2) => {
  return {
    root: css`
      display: flex;
    `,

    tabs: css`
      width: 250px;
    `,

    content: css`
      flex-grow: 1;
      padding-left: 20px;
      border-left: 1px solid ${theme.colors.border.weak};
    `,
  };
};
