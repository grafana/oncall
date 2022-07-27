import React from 'react';

import { getLocationSrv } from '@grafana/runtime';
import { Button, HorizontalGroup, IconButton, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';

import NewScheduleSelector from 'components/NewScheduleSelector/NewScheduleSelector';
import PluginLink from 'components/PluginLink/PluginLink';
import ScheduleFinal from 'components/Rotations/ScheduleFinal';
import ScheduleCounter from 'components/ScheduleCounter/ScheduleCounter';
import SchedulesFilters from 'components/SchedulesFilters_NEW/SchedulesFilters';
import { SchedulesFiltersType } from 'components/SchedulesFilters_NEW/SchedulesFilters.types';
import Table from 'components/Table/Table';
import Text from 'components/Text/Text';
import TimelineMarks from 'components/TimelineMarks/TimelineMarks';
import UserTimezoneSelect from 'components/UserTimezoneSelect/UserTimezoneSelect';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import Rotation from 'containers/Rotation/Rotation';
import { Schedule, ScheduleType } from 'models/schedule/schedule.types';
import { getTzOffsetString } from 'models/timezone/timezone.helpers';
import { Timezone } from 'models/timezone/timezone.types';
import { getStartOfWeek } from 'pages/schedule/Schedule.helpers';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';

import styles from './Schedules.module.css';

const cx = cn.bind(styles);

interface SchedulesPageProps extends WithStoreProps {}

interface SchedulesPageState {
  startMoment: dayjs.Dayjs;
  filters: SchedulesFiltersType;
  showNewScheduleSelector: boolean;
}

@observer
class SchedulesPage extends React.Component<SchedulesPageProps, SchedulesPageState> {
  constructor(props: SchedulesPageProps) {
    super(props);

    const { store } = this.props;
    this.state = {
      startMoment: getStartOfWeek(store.currentTimezone),
      filters: { searchTerm: '', status: 'all', type: 'all' },
      showNewScheduleSelector: false,
    };
  }

  async componentDidMount() {
    const { store } = this.props;

    store.userStore.updateItems();
    store.scheduleStore.updateItems();
  }

  componentDidUpdate() {}

  render() {
    const { store } = this.props;
    const { filters, showNewScheduleSelector } = this.state;

    const { scheduleStore } = store;

    const schedules = scheduleStore.getSearchResult();

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

    const moment = dayjs().tz(store.currentTimezone);

    const users = store.userStore.getSearchResult().results;

    return (
      <>
        <div className={cx('root')}>
          <VerticalGroup>
            <HorizontalGroup justify="space-between">
              <SchedulesFilters value={filters} onChange={this.handleSchedulesFiltersChange} />
              <HorizontalGroup spacing="lg">
                {users && (
                  <UserTimezoneSelect
                    value={store.currentTimezone}
                    users={users}
                    onChange={this.handleTimezoneChange}
                  />
                )}
                <Button size="sm" variant="primary" onClick={this.handleCreateScheduleClick}>
                  + New schedule
                </Button>
              </HorizontalGroup>
            </HorizontalGroup>
            <Table
              columns={columns}
              data={schedules}
              pagination={{ page: 1, total: 1, onChange: this.handlePageChange }}
              rowKey="id"
              expandable={{
                expandedRowRender: this.renderSchedule,
                expandRowByClick: true,
                expandedRowClassName: () => cx('expanded-row'),
              }}
            />
          </VerticalGroup>
        </div>
        {showNewScheduleSelector && (
          <NewScheduleSelector
            onCreate={this.handleCreateSchedule}
            onUpdate={this.update}
            onHide={() => {
              this.setState({ showNewScheduleSelector: false });
            }}
          />
        )}
      </>
    );
  }

  handleTimezoneChange = (value: Timezone) => {
    const { store } = this.props;

    store.currentTimezone = value;

    this.setState({ startMoment: getStartOfWeek(value) });
  };

  handleCreateScheduleClick = () => {
    this.setState({ showNewScheduleSelector: true });
  };

  handleCreateSchedule = (data: Schedule) => {
    const { store } = this.props;

    if (data.type === ScheduleType.API) {
      getLocationSrv().update({ query: { page: 'schedule', id: data.id } });
    }
  };

  renderSchedule = (data: Schedule) => {
    const { startMoment } = this.state;
    const { store } = this.props;

    return (
      <div className={cx('schedule')}>
        <TimelineMarks startMoment={startMoment} />
        <div className={cx('rotations')}>
          <ScheduleFinal
            hideHeader
            scheduleId={data.id}
            currentTimezone={store.currentTimezone}
            startMoment={startMoment}
          />
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
        {/*{item.users.map((user) => (
          <HorizontalGroup spacing="xs">
            <Avatar src={user.avatar} size="large" /> {user.name}
          </HorizontalGroup>
        ))}*/}
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
        <WithConfirm>
          <IconButton tooltip="Delete" name="trash-alt" onClick={this.getDeleteScheduleClickHandler(item.id)} />
        </WithConfirm>
      </HorizontalGroup>
    );
  };

  getDeleteScheduleClickHandler = (id: Schedule['id']) => {
    const { store } = this.props;
    const { scheduleStore } = store;

    return () => {
      scheduleStore.delete(id).then(this.update);
    };
  };

  handleSchedulesFiltersChange = (filters: SchedulesFiltersType) => {
    this.setState({ filters });
  };

  handlePageChange = (page: number) => {};

  update = () => {
    const { store } = this.props;
    const { scheduleStore } = store;

    return scheduleStore.updateItems();
  };
}

export default withMobXProviderContext(SchedulesPage);
