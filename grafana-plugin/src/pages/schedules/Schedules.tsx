import React, { SyntheticEvent } from 'react';

import { Button, HorizontalGroup, IconButton, LoadingPlaceholder, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { debounce } from 'lodash-es';
import { observer } from 'mobx-react';
import { RouteComponentProps, withRouter } from 'react-router-dom';

import Avatar from 'components/Avatar/Avatar';
import { MatchMediaTooltip } from 'components/MatchMediaTooltip/MatchMediaTooltip';
import NewScheduleSelector from 'components/NewScheduleSelector/NewScheduleSelector';
import PluginLink from 'components/PluginLink/PluginLink';
import ScheduleCounter from 'components/ScheduleCounter/ScheduleCounter';
import SchedulesFilters from 'components/SchedulesFilters/SchedulesFilters';
import { SchedulesFiltersType } from 'components/SchedulesFilters/SchedulesFilters.types';
import Table from 'components/Table/Table';
import Text from 'components/Text/Text';
import TimelineMarks from 'components/TimelineMarks/TimelineMarks';
import UserTimezoneSelect from 'components/UserTimezoneSelect/UserTimezoneSelect';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import ScheduleFinal from 'containers/Rotations/ScheduleFinal';
import ScheduleForm from 'containers/ScheduleForm/ScheduleForm';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { Schedule, ScheduleType } from 'models/schedule/schedule.types';
import { getSlackChannelName } from 'models/slack_channel/slack_channel.helpers';
import { Timezone } from 'models/timezone/timezone.types';
import { getStartOfWeek } from 'pages/schedule/Schedule.helpers';
import { WithStoreProps, PageProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import LocationHelper from 'utils/LocationHelper';
import { UserActions } from 'utils/authorization';
import { PLUGIN_ROOT, TABLE_COLUMN_MAX_WIDTH } from 'utils/consts';

import styles from './Schedules.module.css';

const cx = cn.bind(styles);
const FILTERS_DEBOUNCE_MS = 500;
const ITEMS_PER_PAGE = 10;

interface SchedulesPageProps extends WithStoreProps, RouteComponentProps, PageProps {}

interface SchedulesPageState {
  startMoment: dayjs.Dayjs;
  filters: SchedulesFiltersType;
  showNewScheduleSelector: boolean;
  expandedRowKeys: Array<Schedule['id']>;
  scheduleIdToEdit?: Schedule['id'];
  page: number;
}

@observer
class SchedulesPage extends React.Component<SchedulesPageProps, SchedulesPageState> {
  constructor(props: SchedulesPageProps) {
    super(props);

    const { store } = this.props;

    this.state = {
      startMoment: getStartOfWeek(store.currentTimezone),
      filters: { searchTerm: '', type: undefined, used: undefined },
      showNewScheduleSelector: false,
      expandedRowKeys: [],
      scheduleIdToEdit: undefined,
      page: 1,
    };
  }

  async componentDidMount() {
    const {
      store,
      query: { p },
    } = this.props;

    const { filters, page } = this.state;

    await store.scheduleStore.updateItems(filters, page, () => filters === this.state.filters);

    this.setState({ page: p ? Number(p) : 1 }, this.updateSchedules);
  }

  updateSchedules = async () => {
    const { store } = this.props;
    const { filters, page } = this.state;

    LocationHelper.update({ p: page }, 'partial');

    await store.scheduleStore.updateItems(filters, page);
  };

  render() {
    const { store } = this.props;
    const { filters, showNewScheduleSelector, expandedRowKeys, scheduleIdToEdit, page } = this.state;

    const { results, count } = store.scheduleStore.getSearchResult();

    const columns = [
      {
        width: '10%',
        title: 'Type',
        dataIndex: 'type',
        render: this.renderType,
      },
      {
        width: '10%',
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
        width: '50px',
        key: 'buttons',
        render: this.renderButtons,
        className: cx('buttons'),
      },
    ];

    const users = store.userStore.getSearchResult().results;

    return (
      <>
        <div className={cx('root')}>
          <VerticalGroup>
            <div className={cx('schedules__filters-container')}>
              <SchedulesFilters value={filters} onChange={this.handleSchedulesFiltersChange} />
              <div className={cx('schedules__actions')}>
                {users && (
                  <UserTimezoneSelect
                    value={store.currentTimezone}
                    users={users}
                    onChange={this.handleTimezoneChange}
                  />
                )}
                <WithPermissionControlTooltip userAction={UserActions.SchedulesWrite}>
                  <Button variant="primary" onClick={this.handleCreateScheduleClick}>
                    + New schedule
                  </Button>
                </WithPermissionControlTooltip>
              </div>
            </div>
            <Table
              columns={columns}
              data={results}
              loading={!results}
              pagination={{ page, total: Math.ceil((count || 0) / ITEMS_PER_PAGE), onChange: this.handlePageChange }}
              rowKey="id"
              expandable={{
                expandedRowKeys: expandedRowKeys,
                onExpand: this.handleExpandRow,
                expandedRowRender: this.renderSchedule,
                expandRowByClick: true,
              }}
              emptyText={this.renderNotFound()}
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

  renderNotFound() {
    return (
      <div className={cx('loader')}>
        <Text type="secondary">Not found</Text>
      </div>
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
    const { history } = this.props;

    if (data.type === ScheduleType.API) {
      history.push(`${PLUGIN_ROOT}/schedules/${data.id}`);
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
    const { history } = this.props;

    return () => history.push(`${PLUGIN_ROOT}/schedules/${scheduleId}`);
  };

  renderType = (value: number) => {
    type tTypeToVerbal = {
      [key: number]: string;
    };
    const typeToVerbal: tTypeToVerbal = { 0: 'API/Terraform', 1: 'Ical', 2: 'Web' };
    return typeToVerbal[value];
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

        {item.warnings?.length > 0 && (
          <ScheduleCounter
            type="warning"
            addPadding
            count={item.warnings.length}
            tooltipTitle="Warnings"
            tooltipContent={
              <VerticalGroup spacing="none">
                {item.warnings.map((warning, index) => (
                  <Text type="primary" key={index}>
                    {warning}
                  </Text>
                ))}
              </VerticalGroup>
            }
          />
        )}
      </HorizontalGroup>
    );
  };

  renderName = (item: Schedule) => {
    return <PluginLink query={{ page: 'schedules', id: item.id }}>{item.name}</PluginLink>;
  };

  renderOncallNow = (item: Schedule, _index: number) => {
    if (item.on_call_now?.length > 0) {
      return (
        <div className="table__email-column">
          <VerticalGroup>
            {item.on_call_now.map((user) => {
              return (
                <PluginLink key={user.pk} query={{ page: 'users', id: user.pk }} className="table__email-content">
                  <div className={cx('schedules__user-on-call')}>
                    <div>
                      <Avatar size="big" src={user.avatar} />
                    </div>
                    <MatchMediaTooltip placement="top" content={user.username} maxWidth={TABLE_COLUMN_MAX_WIDTH}>
                      <span className="table__email-content">{user.username}</span>
                    </MatchMediaTooltip>
                  </div>
                </PluginLink>
              );
            })}
          </VerticalGroup>
        </div>
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
      /* Wrapper div for onClick event to prevent expanding schedule view on delete/edit click */
      <div onClick={(event: SyntheticEvent) => event.stopPropagation()}>
        <HorizontalGroup>
          <WithPermissionControlTooltip key="edit" userAction={UserActions.SchedulesWrite}>
            <IconButton tooltip="Settings" name="cog" onClick={this.getEditScheduleClickHandler(item.id)} />
          </WithPermissionControlTooltip>
          <WithPermissionControlTooltip key="edit" userAction={UserActions.SchedulesWrite}>
            <WithConfirm>
              <IconButton tooltip="Delete" name="trash-alt" onClick={this.getDeleteScheduleClickHandler(item.id)} />
            </WithConfirm>
          </WithPermissionControlTooltip>
        </HorizontalGroup>
      </div>
    );
  };

  getEditScheduleClickHandler = (id: Schedule['id']) => {
    return () => {
      this.setState({ scheduleIdToEdit: id });
    };
  };

  getDeleteScheduleClickHandler = (id: Schedule['id']) => {
    const { store } = this.props;
    const { scheduleStore } = store;

    return () => {
      scheduleStore.delete(id).then(() => this.update(true));
    };
  };

  handleSchedulesFiltersChange = (filters: SchedulesFiltersType) => {
    this.setState({ filters }, () => this.debouncedUpdateSchedules(filters));
  };

  applyFilters = (filters: SchedulesFiltersType) => {
    const { scheduleStore } = this.props.store;
    const shouldUpdateFn = () => this.state.filters === filters;
    scheduleStore.updateItems(filters, 1, shouldUpdateFn).then(() => {
      if (shouldUpdateFn) {
        this.setState({ page: 1 });
      }
    });
  };

  debouncedUpdateSchedules = debounce(this.applyFilters, FILTERS_DEBOUNCE_MS);

  handlePageChange = (page: number) => {
    this.setState({ page }, this.updateSchedules);
    this.setState({ expandedRowKeys: [] });
  };

  update = (isRemoval = false) => {
    const { store } = this.props;
    const { filters, page } = this.state;
    const { scheduleStore } = store;

    // For removal we need to check if count is 1
    // which means we should change the page to the previous one
    const { results } = store.scheduleStore.getSearchResult();
    const newPage = results.length === 1 ? Math.max(page - 1, 1) : page;

    return scheduleStore.updateItems(filters, isRemoval ? newPage : page);
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

export default withRouter(withMobXProviderContext(SchedulesPage));
