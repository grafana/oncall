import React from 'react';

import { AppRootProps } from '@grafana/data';
import { Alert, Icon, Stack } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import { VerticalTabsBar, VerticalTab } from 'components/VerticalTabsBar/VerticalTabsBar';
import MSTeamsSettings from 'pages/settings/tabs/ChatOps/tabs/MSTeamsSettings/MSTeamsSettings';
import { SlackSettings } from 'pages/settings/tabs/ChatOps/tabs/SlackSettings/SlackSettings';
import TelegramSettings from 'pages/settings/tabs/ChatOps/tabs/TelegramSettings/TelegramSettings';
import { AppFeature } from 'state/features';
import { WithStoreProps } from 'state/types';
import { useStore } from 'state/useStore';
import { withMobXProviderContext } from 'state/withStore';
import { LocationHelper } from 'utils/LocationHelper';

import { handleChatOpsQueryParamError } from './ChatOps.helpers';

import styles from './ChatOps.module.css';

const cx = cn.bind(styles);

export enum ChatOpsTab {
  Slack = 'Slack',
  Telegram = 'Telegram',
  MSTeams = 'MSTeams',
}
interface ChatOpsProps extends AppRootProps, WithStoreProps {}
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
    const { store } = this.props;

    if (!this.isChatOpsConfigured() && store.isOpenSource) {
      return this.renderNoChatOpsBannerInfo();
    }

    return (
      <div className={cx('root')}>
        <div className={cx('tabs')}>
          <Tabs activeTab={activeTab} onTabChange={(tab: ChatOpsTab) => this.handleChatopsTabChange(tab)} />
        </div>
        <div className={cx('content')}>
          <TabsContent activeTab={activeTab} />
        </div>
      </div>
    );
  }

  renderNoChatOpsBannerInfo() {
    return (
      <div className={cx('root')} data-testid="chatops-banner">
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
      store.hasFeature(AppFeature.MsTeams)
    );
  }

  handleChatopsTabChange(tab: ChatOpsTab) {
    this.setState({ activeTab: tab });
    LocationHelper.update({ chatOpsTab: tab }, 'partial');
  }
}

export const ChatOpsPage = withMobXProviderContext(_ChatOpsPage);

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
      {store.hasFeature(AppFeature.Slack) && activeTab === ChatOpsTab.Slack && (
        <div className={cx('messenger-settings')}>
          <SlackSettings />
        </div>
      )}
      {store.hasFeature(AppFeature.Telegram) && activeTab === ChatOpsTab.Telegram && (
        <div className={cx('messenger-settings')}>
          <TelegramSettings />
        </div>
      )}
      {store.hasFeature(AppFeature.MsTeams) && activeTab === ChatOpsTab.MSTeams && (
        <div className={cx('messenger-settings')}>
          <MSTeamsSettings />
        </div>
      )}
    </>
  );
};
