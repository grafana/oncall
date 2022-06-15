import React from 'react';

import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import PluginLink from 'components/PluginLink/PluginLink';
import GSelect from 'containers/GSelect/GSelect';
import { PRIVATE_CHANNEL_NAME } from 'models/slack_channel/slack_channel.config';
import { withMobXProviderContext } from 'state/withStore';

import styles from './Schedule.module.css';

const cx = cn.bind(styles);

interface SchedulePageProps {}

interface SchedulePageState {}

@observer
class SchedulePage extends React.Component<SchedulePageProps, SchedulePageState> {
  async componentDidMount() {}

  componentDidUpdate() {}

  render() {
    return <div className={cx('root')}>Hello!</div>;
  }
}

export default withMobXProviderContext(SchedulePage);
