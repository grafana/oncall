import React from 'react';

import { HorizontalGroup, Icon } from '@grafana/ui';
import cn from 'classnames/bind';

import VerticalTabsBar, { VerticalTab } from 'components/VerticalTabsBar/VerticalTabsBar';
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
