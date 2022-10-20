import React from 'react';

import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import GSelect from 'containers/GSelect/GSelect';
import { PRIVATE_CHANNEL_NAME } from 'models/slack_channel/slack_channel.config';
import { withMobXProviderContext } from 'state/withStore';

import styles from './Test.module.css';
import PluginLink from 'components/PluginLink/PluginLink';
import { PluginPage } from 'PluginPage';
import { pages } from 'pages';

const cx = cn.bind(styles);

@observer
class Test extends React.Component<any, any> {
  async componentDidMount() {}

  componentDidUpdate() {}

  render() {
    return (
      <PluginPage pageNav={pages['test'].getPageNav()}>
        <div className={cx('root')}>
          <GSelect
            isMulti
            showSearch
            allowClear
            modelName="userStore"
            displayField="username"
            valueField="pk"
            placeholder="Select Users"
            className={cx('select', 'control')}
            value={undefined}
            onChange={this.slackChannelChangeHandler}
            nullItemName={PRIVATE_CHANNEL_NAME}
          />
        </div>
      </PluginPage>
    );
  }

  slackChannelChangeHandler = (value: any) => {
    console.log(value);
  };
}

export default withMobXProviderContext(Test);
