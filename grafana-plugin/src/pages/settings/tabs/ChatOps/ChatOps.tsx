import React from 'react';

import { AppRootProps } from '@grafana/data';
import { HorizontalGroup, Icon } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import VerticalTabsBar, { VerticalTab } from 'components/VerticalTabsBar/VerticalTabsBar';
import SlackSettings from 'pages/settings/tabs/ChatOps/tabs/SlackSettings/SlackSettings';
import TelegramSettings from 'pages/settings/tabs/ChatOps/tabs/TelegramSettings/TelegramSettings';
import { AppFeature } from 'state/features';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import LocationHelper from 'utils/LocationHelper';

import styles from './ChatOps.module.css';

const cx = cn.bind(styles);

export enum ChatOpsTab {
  Slack = 'Slack',
  Telegram = 'Telegram',
}
interface ChatOpsProps extends AppRootProps, WithStoreProps {}
interface ChatOpsState {
  activeTab: ChatOpsTab;
}

@observer
class ChatOpsPage extends React.Component<ChatOpsProps, ChatOpsState> {
  state: ChatOpsState = {
    activeTab: ChatOpsTab.Slack,
  };

  componentDidMount() {
    const { query } = this.props;

    this.handleChatopsTabChange(query?.tab || ChatOpsTab.Slack);
  }

  componentWillUnmount() {
    this.handleChatopsTabChange(undefined);
  }

  render() {
    const { activeTab } = this.state;
    const { store } = this.props;

    return (
      <div className={cx('root')}>
        <div className={cx('tabs')}>
          <Tabs
            activeTab={activeTab}
            onTabChange={(tab: ChatOpsTab) => this.handleChatopsTabChange(tab)}
            store={store}
          />
        </div>
        <div className={cx('content')}>
          <TabsContent activeTab={activeTab} store={store} />
        </div>
      </div>
    );
  }

  handleChatopsTabChange(tab: ChatOpsTab) {
    this.setState({ activeTab: tab });
    LocationHelper.update({ tab: tab }, 'partial');
  }
}

export default withMobXProviderContext(ChatOpsPage);

interface TabsProps extends WithStoreProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

const Tabs = (props: TabsProps) => {
  const { activeTab, onTabChange } = props;
  const { store } = props;

  return (
    <VerticalTabsBar activeTab={activeTab} onChange={onTabChange}>
      {store.hasFeature(AppFeature.Slack) && (
        <VerticalTab id={ChatOpsTab.Slack}>
          <HorizontalGroup>
            <Icon name="slack" />
            Slack
          </HorizontalGroup>
        </VerticalTab>
      )}

      {store.hasFeature(AppFeature.Telegram) && (
        <VerticalTab id={ChatOpsTab.Telegram}>
          <HorizontalGroup>
            <Icon name="message" />
            Telegram
          </HorizontalGroup>
        </VerticalTab>
      )}
    </VerticalTabsBar>
  );
};

interface TabsContentProps extends WithStoreProps {
  activeTab: string;
}

const TabsContent = (props: TabsContentProps) => {
  const { activeTab, store } = props;

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
    </>
  );
};
