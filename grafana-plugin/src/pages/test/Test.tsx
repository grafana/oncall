import React from 'react';

import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import GSelect from 'containers/GSelect/GSelect';
import { PRIVATE_CHANNEL_NAME } from 'models/slack_channel/slack_channel.config';
import { withMobXProviderContext } from 'state/withStore';

import styles from './Test.module.css';

const cx = cn.bind(styles);

@observer
class Test extends React.Component<any, any> {
  async componentDidMount() {}

  componentDidUpdate() {}

  render() {
    return (
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
    );
  }

  slackChannelChangeHandler = (value: any) => {
    console.log(value);
  };
}

export default withMobXProviderContext(Test);
