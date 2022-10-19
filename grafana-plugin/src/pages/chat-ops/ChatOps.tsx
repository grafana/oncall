import React from 'react';

import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import { Tabs, TabsContent } from 'pages/chat-ops/parts';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';

import { ChatOpsTab } from './ChatOps.types';

import styles from './ChatOps.module.css';
import { PluginPage } from 'PluginPage';

const cx = cn.bind(styles);

interface MessengersPageProps extends WithStoreProps {}

interface MessengersPageState {
  activeTab: ChatOpsTab;
}

@observer
class ChatOpsPage extends React.Component<MessengersPageProps, MessengersPageState> {
  state: MessengersPageState = {
    activeTab: ChatOpsTab.Slack,
  };

  render() {
    const { store } = this.props;
    const { activeTab } = this.state;
    const { teamStore } = store;

    return (
      <PluginPage>
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
      </PluginPage>
    );
  }
}

export default withMobXProviderContext(ChatOpsPage);
