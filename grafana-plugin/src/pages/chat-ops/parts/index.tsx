import React from 'react';

import { HorizontalGroup, Icon, Tab, TabsBar } from '@grafana/ui';
import cn from 'classnames/bind';

import { ChatOpsTab } from 'pages/chat-ops/ChatOps.types';

import SlackSettings from './tabs/SlackSettings/SlackSettings';
import TelegramSettings from './tabs/TelegramSettings/TelegramSettings';

import styles from 'containers/UserSettings/parts/index.module.css';

const cx = cn.bind(styles);

interface TabsProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

export const Tabs = (props: TabsProps) => {
  const { activeTab, onTabChange } = props;

  return (
    <TabsBar>
      <Tab
        key={ChatOpsTab.Slack}
        onChangeTab={() => onTabChange(ChatOpsTab.Slack)}
        active={activeTab === ChatOpsTab.Slack}
        label={"Slack"}
      >
        <Icon name="slack" /> Slack
      </Tab>
      <Tab
        key={ChatOpsTab.Telegram}
        onChangeTab={() => onTabChange(ChatOpsTab.Telegram)}
        active={activeTab === ChatOpsTab.Telegram}
        label={"Telegram"}
      >
        <Icon name="message" /> Telegram
      </Tab>
    </TabsBar>
  );
};

interface TabsContentProps {
  activeTab: string;
}

export const TabsContent = (props: TabsContentProps) => {
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
