import React from 'react';

import { AppRootProps } from '@grafana/data';
import { getLocationSrv } from '@grafana/runtime';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import { Tabs, TabsContent } from 'pages/chat-ops/parts';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';

import { ChatOpsTab } from './ChatOps.types';

import styles from './ChatOps.module.css';

const cx = cn.bind(styles);

interface MessengersPageProps extends WithStoreProps, AppRootProps {}

interface MessengersPageState {
  activeTab: ChatOpsTab;
}

@observer
class ChatOpsPage extends React.Component<MessengersPageProps, MessengersPageState> {
  state: MessengersPageState = {
    activeTab: ChatOpsTab.Slack,
  };

  componentDidMount() {
    const { query } = this.props;

    if (query.tab) {
      this.setState({ activeTab: query.tab });
      getLocationSrv().update({ partial: true, query: { tab: query.tab } });
    } else {
      this.setState({ activeTab: ChatOpsTab.Slack });
      getLocationSrv().update({ partial: true, query: { tab: ChatOpsTab.Slack } });
    }
  }

  render() {
    const { activeTab } = this.state;

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

  handleChatopsTabChange(tab: ChatOpsTab) {
    this.setState({ activeTab: tab });
    getLocationSrv().update({ partial: true, query: { tab: tab } });
  }
}

export default withMobXProviderContext(ChatOpsPage);
