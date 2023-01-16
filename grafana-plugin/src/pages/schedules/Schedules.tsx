import React from 'react';

import { Button, HorizontalGroup, IconButton, LoadingPlaceholder, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { debounce } from 'lodash-es';
import { observer } from 'mobx-react';

import Avatar from 'components/Avatar/Avatar';
import NewScheduleSelector from 'components/NewScheduleSelector/NewScheduleSelector';
import PluginLink from 'components/PluginLink/PluginLink';
import ScheduleCounter from 'components/ScheduleCounter/ScheduleCounter';
import ScheduleWarning from 'components/ScheduleWarning/ScheduleWarning';
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
import { Schedule, ScheduleType } from 'models/schedule/schedule.types';
import { getSlackChannelName } from 'models/slack_channel/slack_channel.helpers';
import { Timezone } from 'models/timezone/timezone.types';
import { getStartOfWeek } from 'pages/schedule/Schedule.helpers';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import LocationHelper from 'utils/LocationHelper';
import { UserActions } from 'utils/authorization';

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
      filters: { searchTerm: '', status: 'all', type: undefined },
      showNewScheduleSelector: false,
      expandedRowKeys: [],
      scheduleIdToEdit: undefined,
    };
  }

  async componentDidMount() {
    const { store } = this.props;

    store.userStore.updateItems();
    store.scheduleStore.updateItems();
  }

  render() {
    const { store } = this.props;
    const { filters, showNewScheduleSelector, expandedRowKeys, scheduleIdToEdit } = this.state;

    const { scheduleStore } = store;

    const schedules = scheduleStore.getSearchResult();
    const columns = [
      {
        width: '10%',
        title: 'Type',
        dataIndex: 'type',
        render: this.renderType,
      },
      {
        width: '5%',
        title: 'Status',
        key: 'name',
        render: (item: Schedule) => this.renderStatus(item),
      },
      {
        width: '30%',
        title: 'Name',
        key: 'name',
        render: this.renderName,
      },
      {
        width: '30%',
        title: 'Oncall',
        key: 'users',
        render: this.renderOncallNow,
      },
      {
        width: '10%',
        title: 'Slack channel',
        render: this.renderChannelName,
      },
      {
        width: '10%',
        title: 'Slack user group',
        render: this.renderUserGroup,
      },
      {
        width: '5%',
        key: 'warning',
        render: this.renderWarning,
      },
      {
        width: '50px',
        key: 'buttons',
        render: this.renderButtons,
        className: cx('buttons'),
      },
    ];

    const users = store.userStore.getSearchResult().results;

    const data = schedules
      ? schedules.filter(
          (schedule) =>
            filters.status === 'all' ||
            (filters.status === 'used' && schedule.number_of_escalation_chains) ||
            (filters.status === 'unused' && !schedule.number_of_escalation_chains)
        )
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
                <WithPermissionControl userAction={UserActions.SchedulesWrite}>
                  <Button variant="primary" onClick={this.handleCreateScheduleClick}>
                    + New schedule
                  </Button>
                </WithPermissionControl>
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
    if (data.type === ScheduleType.API) {
      LocationHelper.update({ page: 'schedule', id: data.id }, 'partial');
    }
  };

  handleExpandRow = (expanded: boolean, data: Schedule) => {
    const { expandedRowKeys } = this.state;

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
    return () => LocationHelper.update({ page: 'schedule', id: scheduleId }, 'replace');
  };

  renderType = (value: number) => {
    type tTypeToVerbal = {
      [key: number]: string;
    };
    const typeToVerbal: tTypeToVerbal = { 0: 'API/Terraform', 1: 'Ical', 2: 'Web' };
    return typeToVerbal[value];
  };

  renderWarning = (item: Schedule) => {
    return <ScheduleWarning item={item} />;
  };

  renderStatus = (item: Schedule) => {
    const {
      store: { scheduleStore },
    } = this.props;

    const relatedEscalationChains = scheduleStore.relatedEscalationChains[item.id];
    return (
      <HorizontalGroup>
        {item.number_of_escalation_chains > 0 && (
          <ScheduleCounter
            type="link"
            count={item.number_of_escalation_chains}
            tooltipTitle="Used in escalations"
            tooltipContent={
              <VerticalGroup spacing="sm">
                {relatedEscalationChains ? (
                  relatedEscalationChains.length ? (
                    relatedEscalationChains.map((escalationChain) => (
                      <div key={escalationChain.pk}>
                        <PluginLink query={{ page: 'escalations', id: escalationChain.pk }}>
                          {escalationChain.name}
                        </PluginLink>
                      </div>
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
        )}

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

  renderOncallNow = (item: Schedule, _index: number) => {
    if (item.on_call_now?.length > 0) {
      return (
        <VerticalGroup>
          {item.on_call_now.map((user, _index) => {
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

  renderChannelName = (value: Schedule) => {
    return getSlackChannelName(value.slack_channel) || '-';
  };

  renderUserGroup = (value: Schedule) => {
    return value.user_group?.handle || '-';
  };

  renderButtons = (item: Schedule) => {
    return (
      <HorizontalGroup>
        <WithPermissionControl key="edit" userAction={UserActions.SchedulesWrite}>
          <IconButton tooltip="Settings" name="cog" onClick={this.getEditScheduleClickHandler(item.id)} />
        </WithPermissionControl>
        <WithPermissionControl key="edit" userAction={UserActions.SchedulesWrite}>
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

    return () => {
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
    scheduleStore.updateItems(filters);
  };

  debouncedUpdateSchedules = debounce(this.applyFilters, 1000);

  handlePageChange = (_page: number) => {};

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
