import React from 'react';

import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import PluginLink from 'components/PluginLink/PluginLink';
import GSelect from 'containers/GSelect/GSelect';
import { PRIVATE_CHANNEL_NAME } from 'models/slack_channel/slack_channel.config';
import { withMobXProviderContext } from 'state/withStore';

import styles from './Schedules.module.css';

const cx = cn.bind(styles);

interface SchedulesPageProps {}

interface SchedulesPageState {}

@observer
class SchedulesPage extends React.Component<SchedulesPageProps, SchedulesPageState> {
  async componentDidMount() {}

  componentDidUpdate() {}

  render() {
    return (
      <div className={cx('root')}>
        <PluginLink query={{ page: 'schedule', id: '1' }}>Schedule 1</PluginLink>
      </div>
    );
  }
}

export default withMobXProviderContext(SchedulesPage);
