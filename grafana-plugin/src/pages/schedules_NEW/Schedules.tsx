import React from 'react';

import { Button, HorizontalGroup, IconButton, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';

import Avatar from 'components/Avatar/Avatar';
import PluginLink from 'components/PluginLink/PluginLink';
import { getColor, getLabel } from 'components/Rotations/Rotations.helpers';
import ScheduleCounter from 'components/ScheduleCounter/ScheduleCounter';
import SchedulesFilters from 'components/SchedulesFilters_NEW/SchedulesFilters';
import { SchedulesFiltersType } from 'components/SchedulesFilters_NEW/SchedulesFilters.types';
import Table from 'components/Table/Table';
import Text from 'components/Text/Text';
import TimelineMarks from 'components/TimelineMarks/TimelineMarks';
import GSelect from 'containers/GSelect/GSelect';
import Rotation from 'containers/Rotation/Rotation';
import { Schedule } from 'models/schedule/schedule.types';
import { PRIVATE_CHANNEL_NAME } from 'models/slack_channel/slack_channel.config';
import { getTzOffsetString } from 'models/timezone/timezone.helpers';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';

import { getRandomSchedules, getRandomTimeslots } from './Schedules.helpers';

import styles from './Schedules.module.css';

const cx = cn.bind(styles);

interface SchedulesPageProps extends WithStoreProps {}

interface SchedulesPageState {
  startMoment: dayjs.Dayjs;
  filters: SchedulesFiltersType;
}

@observer
class SchedulesPage extends React.Component<SchedulesPageProps, SchedulesPageState> {
  state: SchedulesPageState = {
    startMoment: dayjs().utc().startOf('week'),
    schedules: getRandomSchedules(),
    filters: { searchTerm: '', status: 'all', type: 'all' },
  };

  async componentDidMount() {
    const { store } = this.props;

    store.userStore.updateItems();
  }

  componentDidUpdate() {}

  render() {
    const { schedules, filters } = this.state;

    const columns = [
      {
        width: '10%',
        title: 'Status',
        key: 'name',
        render: this.renderStatus,
      },
      {
        width: '30%',
        title: 'Name',
        key: 'name',
        render: this.renderName,
      },
      {
        width: '30%',
        title: 'OnCall',
        key: 'users',
        render: this.renderUsers,
      },
      {
        width: '20%',
        title: 'ChatOps',
        key: 'chatops',
        render: this.renderChatOps,
      },
      {
        width: '10%',
        title: 'Quality',
        key: 'quality',
        render: this.renderQuality,
      },
      {
        key: 'buttons',
        render: this.renderButtons,
      },
    ];

    const moment = dayjs();

    return (
      <div className={cx('root')}>
        <VerticalGroup>
          <HorizontalGroup justify="space-between">
            <SchedulesFilters value={filters} onChange={this.handleSchedulesFiltersChange} />
            <HorizontalGroup spacing="lg">
              <HorizontalGroup>
                <Text type="secondary">Timezone:</Text>
                <Text type="primary">
                  {getTzOffsetString(moment)} ({dayjs.tz.guess()})
                </Text>
              </HorizontalGroup>
              <Button variant="primary">+ New schedule</Button>
            </HorizontalGroup>
          </HorizontalGroup>
          <Table
            columns={columns}
            data={schedules}
            pagination={{ page: 2, total: 100, onChange: this.handlePageChange }}
            rowKey="id"
            expandable={{
              expandedRowRender: this.renderSchedule,
              expandRowByClick: true,
              expandedRowClassName: () => cx('expanded-row'),
            }}
          />
        </VerticalGroup>
      </div>
    );
  }

  renderSchedule = () => {
    const { startMoment } = this.state;

    return (
      <div className={cx('schedule')}>
        <TimelineMarks startMoment={startMoment} />
        <div className={cx('rotations')}>
          <Rotation startMoment={startMoment} id={`${1}-${2}`} layerIndex={1} rotationIndex={2} />
        </div>
      </div>
    );
  };

  renderStatus = () => {
    const escalationsCount = Math.floor(Math.random() * 10) + 1;
    const warningsCount = Math.floor(Math.random() * 10) + 1;

    return (
      <HorizontalGroup>
        <ScheduleCounter
          type="link"
          count={escalationsCount}
          tooltipTitle="Used in escalations"
          tooltipContent={
            <>
              <PluginLink query={{ page: 'integrations', id: 'CXBEG63MBJMDL' }}>Grafana 1</PluginLink>
              <br />
              <PluginLink query={{ page: 'integrations', id: 'CXBEG63MBJMDL' }}>Grafana 2</PluginLink>
              <br />
              <PluginLink query={{ page: 'integrations', id: 'CXBEG63MBJMDL' }}>Grafana 3</PluginLink>
            </>
          }
        />
        <ScheduleCounter
          type="warning"
          count={warningsCount}
          tooltipTitle="Warnings"
          tooltipContent="Schedule has unassigned time periods during next 7 days"
        />
      </HorizontalGroup>
    );
  };

  renderName = (item: Schedule) => {
    return <PluginLink query={{ page: 'schedule', id: item.id }}>{item.name}</PluginLink>;
  };

  renderUsers = (item: Schedule) => {
    return (
      <HorizontalGroup>
        {item.users.map((user) => (
          <HorizontalGroup spacing="xs">
            <Avatar src={user.avatar} size="large" /> {user.name}
          </HorizontalGroup>
        ))}
      </HorizontalGroup>
    );
  };

  renderChatOps = (item: Schedule) => {
    return item.chatOps;
  };

  renderQuality = (item: Schedule) => {
    const type = item.quality > 70 ? 'primary' : 'warning';

    return <Text type={type}>{item.quality}%</Text>;
  };

  renderButtons = (item: Schedule) => {
    return (
      <HorizontalGroup>
        <IconButton tooltip="Copy" name="copy" />
        <IconButton tooltip="Settings" name="cog" />
        <IconButton tooltip="Code" name="brackets-curly" />
        <IconButton tooltip="Delete" name="trash-alt" />
      </HorizontalGroup>
    );
  };

  handleSchedulesFiltersChange = (filters: SchedulesFiltersType) => {
    this.setState({ filters });
  };

  handlePageChange = (page: number) => {};
}

export default withMobXProviderContext(SchedulesPage);
