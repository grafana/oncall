import React from 'react';

import { HorizontalGroup, Icon } from '@grafana/ui';
import cn from 'classnames/bind';

import SlackSettings from 'pages/settings/tabs/ChatOps/tabs/SlackSettings/SlackSettings';
import TelegramSettings from 'pages/settings/tabs/ChatOps/tabs/TelegramSettings/TelegramSettings';

import styles from './ChatOps.module.css';
import { observer } from 'mobx-react';
import { withMobXProviderContext } from 'state/withStore';
import VerticalTabsBar, { VerticalTab } from 'components/VerticalTabsBar/VerticalTabsBar';

const cx = cn.bind(styles);

export enum ChatOpsTab {
  Slack = 'Slack',
  Telegram = 'Telegram',
}

interface ChatOpsState {
  activeTab: ChatOpsTab;
}

@observer
class ChatOpsPage extends React.Component<{}, ChatOpsState> {
  state: ChatOpsState = {
    activeTab: ChatOpsTab.Slack,
  };

  render() {
    const { activeTab } = this.state;

    return (
      <div className={cx('root')}>
        <div className={cx('tabs')}>
          <Tabs
            activeTab={activeTab}
            onTabChange={(tab: ChatOpsTab) => {
              this.setState({ activeTab: tab });
            }}
          />
        </div>
        <div className={cx('content')}>
          <TabsContent activeTab={activeTab} />
        </div>
      </div>
    );
  }
}

export default withMobXProviderContext(ChatOpsPage);

interface TabsProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

const Tabs = (props: TabsProps) => {
  const { activeTab, onTabChange } = props;

  return (
    <VerticalTabsBar activeTab={activeTab} onChange={onTabChange}>
      <VerticalTab id={ChatOpsTab.Slack}>
        <HorizontalGroup>
          <Icon name="slack" />
          Slack
        </HorizontalGroup>
      </VerticalTab>
      <VerticalTab id={ChatOpsTab.Telegram}>
        <HorizontalGroup>
          <Icon name="message" />
          Telegram
        </HorizontalGroup>
      </VerticalTab>
    </VerticalTabsBar>
  );
};

interface TabsContentProps {
  activeTab: string;
}

const TabsContent = (props: TabsContentProps) => {
  const { activeTab } = props;

  return (
    <>
      {activeTab === ChatOpsTab.Slack && (
        <div className={cx('messenger-settings')}>
          <SlackSettings />
        </div>
      )}
      {activeTab === ChatOpsTab.Telegram && (
        <div className={cx('messenger-settings')}>
          <TelegramSettings />
        </div>
      )}
    </>
  );
};
