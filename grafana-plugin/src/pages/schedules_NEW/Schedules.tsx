import React, { SyntheticEvent } from 'react';

import { getLocationSrv } from '@grafana/runtime';
import { Button, HorizontalGroup, IconButton, LoadingPlaceholder, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { debounce } from 'lodash-es';
import { observer } from 'mobx-react';

import Avatar from 'components/Avatar/Avatar';
import NewScheduleSelector from 'components/NewScheduleSelector/NewScheduleSelector';
import PluginLink from 'components/PluginLink/PluginLink';
import ScheduleCounter from 'components/ScheduleCounter/ScheduleCounter';
import SchedulesFilters from 'components/SchedulesFilters_NEW/SchedulesFilters';
import { SchedulesFiltersType } from 'components/SchedulesFilters_NEW/SchedulesFilters.types';
import Table from 'components/Table/Table';
import Text from 'components/Text/Text';
import TimelineMarks from 'components/TimelineMarks/TimelineMarks';
import UserTimezoneSelect from 'components/UserTimezoneSelect/UserTimezoneSelect';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import ScheduleFinal from 'containers/Rotations/ScheduleFinal';
import ScheduleForm from 'containers/ScheduleForm/ScheduleForm';
import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { getFromString } from 'models/schedule/schedule.helpers';
import { Schedule, ScheduleType } from 'models/schedule/schedule.types';
import { Timezone } from 'models/timezone/timezone.types';
import { getStartOfWeek } from 'pages/schedule/Schedule.helpers';
import { AppFeature } from 'state/features';
import { WithStoreProps } from 'state/types';
import { UserAction } from 'state/userAction';
import { withMobXProviderContext } from 'state/withStore';

import styles from './Schedules.module.css';

const cx = cn.bind(styles);

interface SchedulesPageProps extends WithStoreProps {}

interface SchedulesPageState {
  startMoment: dayjs.Dayjs;
  filters: SchedulesFiltersType;
  showNewScheduleSelector: boolean;
  expandedRowKeys: Array<Schedule['id']>;
  scheduleIdToEdit?: Schedule['id'];
}

@observer
class SchedulesPage extends React.Component<SchedulesPageProps, SchedulesPageState> {
  constructor(props: SchedulesPageProps) {
    super(props);

    const { store } = this.props;
    this.state = {
      startMoment: getStartOfWeek(store.currentTimezone),
      filters: { searchTerm: '', status: 'all', type: ScheduleType.API },
      showNewScheduleSelector: false,
      expandedRowKeys: [],
      scheduleIdToEdit: undefined,
    };
  }

  async componentDidMount() {
    const { store } = this.props;

    /* if (!store.hasFeature(AppFeature.WebSchedules)) {
      getLocationSrv().update({ query: { page: 'schedules' } });
    } */

    store.userStore.updateItems();
    store.scheduleStore.updateItems();
  }

  render() {
    const { store } = this.props;
    const { filters, showNewScheduleSelector, expandedRowKeys, scheduleIdToEdit } = this.state;

    const { scheduleStore } = store;

    const schedules = scheduleStore.getSearchResult(/*filters.searchTerm*/);
    const columns = [
      {
        width: '10%',
        title: 'Status',
        key: 'name',
        render: this.renderStatus,
      },
      {
        width: '40%',
        title: 'Name',
        key: 'name',
        render: this.renderName,
      },
      {
        width: '45%',
        title: 'Oncall',
        key: 'users',
        render: this.renderOncallNow,
      },
      /* {
        width: '20%',
        title: 'ChatOps',
        key: 'chatops',
        render: this.renderChatOps,
      },*/
      /*{
        width: '10%',
        title: 'Quality',
        key: 'quality',
        render: this.renderQuality,
      },*/
      {
        width: '5%',
        key: 'buttons',
        render: this.renderButtons,
      },
    ];

    const users = store.userStore.getSearchResult().results;

    const data = schedules
      ? schedules
          .filter((schedule) => schedule.type === ScheduleType.API)
          .filter(
            (schedule) =>
              filters.status === 'all' ||
              (filters.status === 'used' && schedule.number_of_escalation_chains) ||
              (filters.status === 'unused' && !schedule.number_of_escalation_chains)
          )
          .filter((schedule) => !filters.searchTerm || schedule.name.includes(filters.searchTerm))
      : undefined;

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
                <Button variant="primary" onClick={this.handleCreateScheduleClick}>
                  + New schedule
                </Button>
              </HorizontalGroup>
            </HorizontalGroup>
            <Table
              columns={columns}
              data={data}
              pagination={{ page: 1, total: 1, onChange: this.handlePageChange }}
              rowKey="id"
              expandable={{
                expandedRowKeys: expandedRowKeys,
                onExpand: this.handleExpandRow,
                expandedRowRender: this.renderSchedule,
                expandRowByClick: true,
              }}
              emptyText={
                <div className={cx('loader')}>
                  {data ? <Text type="secondary">Not found</Text> : <Text type="secondary">Loading schedules...</Text>}
                </div>
              }
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
        {scheduleIdToEdit && (
          <ScheduleForm
            id={scheduleIdToEdit}
            onUpdate={this.update}
            onHide={() => {
              this.setState({ scheduleIdToEdit: undefined });
            }}
          />
        )}
      </>
    );
  }

  handleTimezoneChange = (value: Timezone) => {
    const { store } = this.props;

    store.currentTimezone = value;

    this.setState({ startMoment: getStartOfWeek(value) }, this.updateEvents);
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

  handleExpandRow = (expanded: boolean, data: Schedule) => {
    const { store } = this.props;
    const { expandedRowKeys } = this.state;
    const { startMoment } = this.state;
    if (expanded && !expandedRowKeys.includes(data.id)) {
      this.setState({ expandedRowKeys: [...this.state.expandedRowKeys, data.id] }, this.updateEvents);
    } else if (!expanded && expandedRowKeys.includes(data.id)) {
      const index = expandedRowKeys.indexOf(data.id);
      const newExpandedRowKeys = [...expandedRowKeys];
      newExpandedRowKeys.splice(index, 1);
      this.setState({ expandedRowKeys: newExpandedRowKeys }, this.updateEvents);
    }
  };

  updateEvents = () => {
    const { store } = this.props;
    const { expandedRowKeys, startMoment } = this.state;

    expandedRowKeys.forEach((scheduleId) => {
      store.scheduleStore.updateEvents(scheduleId, startMoment, 'rotation');
      store.scheduleStore.updateEvents(scheduleId, startMoment, 'override');
      store.scheduleStore.updateEvents(scheduleId, startMoment, 'final');
    });
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
            onClick={this.getScheduleClickHandler(data.id)}
          />
        </div>
      </div>
    );
  };

  getScheduleClickHandler = (scheduleId: Schedule['id']) => {
    return () => {
      getLocationSrv().update({ query: { page: 'schedule', id: scheduleId } });
    };
  };

  renderStatus = (item: Schedule) => {
    const {
      store: { scheduleStore },
    } = this.props;

    const relatedEscalationChains = scheduleStore.relatedEscalationChains[item.id];

    return (
      <HorizontalGroup>
        <ScheduleCounter
          type="link"
          count={item.number_of_escalation_chains}
          tooltipTitle="Used in escalations"
          tooltipContent={
            <VerticalGroup spacing="sm">
              {relatedEscalationChains ? (
                relatedEscalationChains.length ? (
                  relatedEscalationChains.map((escalationChain) => (
                    <PluginLink query={{ page: 'escalations', id: escalationChain.pk }}>
                      {escalationChain.name}
                    </PluginLink>
                  ))
                ) : (
                  'Not used yet'
                )
              ) : (
                <LoadingPlaceholder>Loading related escalation chains....</LoadingPlaceholder>
              )}
            </VerticalGroup>
          }
          onHover={this.getUpdateRelatedEscalationChainsHandler(item.id)}
        />
        {/* <ScheduleCounter
          type="warning"
          count={warningsCount}
          tooltipTitle="Warnings"
          tooltipContent="Schedule has unassigned time periods during next 7 days"
        />*/}
      </HorizontalGroup>
    );
  };

  renderName = (item: Schedule) => {
    return <PluginLink query={{ page: 'schedule', id: item.id }}>{item.name}</PluginLink>;
  };

  renderOncallNow = (item: Schedule, index: number) => {
    if (item.on_call_now?.length > 0) {
      return (
        <VerticalGroup>
          {item.on_call_now.map((user, index) => {
            return (
              <PluginLink key={user.pk} query={{ page: 'users', id: user.pk }}>
                <div>
                  <Avatar size="big" src={user.avatar} />
                  <Text type="secondary"> {user.username}</Text>
                </div>
              </PluginLink>
            );
          })}
        </VerticalGroup>
      );
    }
    return null;
  };

  /* renderChatOps = (item: Schedule) => {
    return item.chatOps;
  }; */

  /* renderQuality = (item: Schedule) => {
    const type = item.quality > 70 ? 'primary' : 'warning';

    return <Text type={type}>{item.quality || 70}%</Text>;
  }; */

  renderButtons = (item: Schedule) => {
    return (
      <HorizontalGroup>
        {/*<IconButton tooltip="Copy" name="copy" />
        <IconButton tooltip="Settings" name="cog" />
        <IconButton tooltip="Code" name="brackets-curly" />*/}
        <WithPermissionControl key="edit" userAction={UserAction.UpdateSchedules}>
          <IconButton tooltip="Settings" name="cog" onClick={this.getEditScheduleClickHandler(item.id)} />
        </WithPermissionControl>
        <WithPermissionControl key="edit" userAction={UserAction.UpdateSchedules}>
          <WithConfirm>
            <IconButton tooltip="Delete" name="trash-alt" onClick={this.getDeleteScheduleClickHandler(item.id)} />
          </WithConfirm>
        </WithPermissionControl>
      </HorizontalGroup>
    );
  };

  getEditScheduleClickHandler = (id: Schedule['id']) => {
    return (event) => {
      event.stopPropagation();

      this.setState({ scheduleIdToEdit: id });
    };
  };

  getDeleteScheduleClickHandler = (id: Schedule['id']) => {
    const { store } = this.props;
    const { scheduleStore } = store;

    return (event: SyntheticEvent) => {
      event.stopPropagation();

      scheduleStore.delete(id).then(this.update);
    };
  };

  handleSchedulesFiltersChange = (filters: SchedulesFiltersType) => {
    this.setState({ filters }, this.debouncedUpdateSchedules);
  };

  applyFilters = () => {
    const { filters } = this.state;
    const { store } = this.props;
    const { scheduleStore } = store;

    // scheduleStore.updateItems(filters.searchTerm);
  };

  debouncedUpdateSchedules = debounce(this.applyFilters, 1000);

  handlePageChange = (page: number) => {};

  update = () => {
    const { store } = this.props;
    const { scheduleStore } = store;

    return scheduleStore.updateItems();
  };

  getUpdateRelatedEscalationChainsHandler = (scheduleId: Schedule['id']) => {
    const { store } = this.props;
    const { scheduleStore } = store;

    return () => {
      scheduleStore.updateRelatedEscalationChains(scheduleId).then(() => {
        this.forceUpdate();
      });
    };
  };
}

export default withMobXProviderContext(SchedulesPage);
