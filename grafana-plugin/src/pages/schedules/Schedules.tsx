import React, { SyntheticEvent } from 'react';

import { AppRootProps } from '@grafana/data';
import { getLocationSrv } from '@grafana/runtime';
import {
  Button,
  ConfirmModal,
  HorizontalGroup,
  Icon,
  LoadingPlaceholder,
  Modal,
  PENDING_COLOR,
  Tooltip,
  VerticalGroup,
} from '@grafana/ui';
import cn from 'classnames/bind';
import { omit } from 'lodash-es';
import { observer } from 'mobx-react';
import moment from 'moment-timezone';

import instructionsImage from 'assets/img/events_instructions.png';
import Avatar from 'components/Avatar/Avatar';
import GTable from 'components/GTable/GTable';
import PageErrorHandlingWrapper, { PageBaseState } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper';
import {
  getWrongTeamResponseInfo,
  initErrorDataState,
} from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper.helpers';
import PluginLink from 'components/PluginLink/PluginLink';
import SchedulesFilters from 'components/SchedulesFilters/SchedulesFilters';
import { SchedulesFiltersType } from 'components/SchedulesFilters/SchedulesFilters.types';
import Text from 'components/Text/Text';
import Tutorial from 'components/Tutorial/Tutorial';
import { TutorialStep } from 'components/Tutorial/Tutorial.types';
import ScheduleForm from 'containers/ScheduleForm/ScheduleForm';
import ScheduleICalSettings from 'containers/ScheduleIcalLink/ScheduleIcalLink';
import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { Schedule, ScheduleEvent, ScheduleType } from 'models/schedule/schedule.types';
import { getSlackChannelName } from 'models/slack_channel/slack_channel.helpers';
import { WithStoreProps } from 'state/types';
import { UserAction } from 'state/userAction';
import { withMobXProviderContext } from 'state/withStore';
import { openErrorNotification } from 'utils';

import { getDatesString } from './Schedules.helpers';

import styles from './Schedules.module.css';
import { PluginPage } from 'PluginPage';

const cx = cn.bind(styles);

interface SchedulesPageProps extends WithStoreProps, AppRootProps {}
interface SchedulesPageState extends PageBaseState {
  scheduleIdToEdit?: Schedule['id'];
  scheduleIdToDelete?: Schedule['id'];
  scheduleIdToExport?: Schedule['id'];
  filters: SchedulesFiltersType;
  expandedSchedulesKeys: Array<Schedule['id']>;
}

@observer
class SchedulesPage extends React.Component<SchedulesPageProps, SchedulesPageState> {
  state: SchedulesPageState = {
    filters: {
      selectedDate: moment().startOf('day').format('YYYY-MM-DD'),
    },
    expandedSchedulesKeys: [],
    errorData: initErrorDataState(),
  };

  componentDidMount() {
    this.update().then(this.parseQueryParams);
  }

  componentDidUpdate(prevProps: SchedulesPageProps) {
    if (this.props.query.id !== prevProps.query.id) {
      this.parseQueryParams();
    }
  }

  parseQueryParams = async () => {
    this.setState({ errorData: initErrorDataState() }); // reset wrong team error to false on query parse

    const {
      store,
      query: { id },
    } = this.props;

    if (!id) {
      return;
    }

    let scheduleId: string = undefined;
    const isNewSchedule = id === 'new';

    if (!isNewSchedule) {
      // load schedule only for valid id
      const schedule = await store.scheduleStore
        .loadItem(id, true)
        .catch((error) => this.setState({ errorData: { ...getWrongTeamResponseInfo(error) } }));
      if (!schedule) {
        return;
      }

      scheduleId = schedule.id;
    }

    if (scheduleId || isNewSchedule) {
      this.setState({ scheduleIdToEdit: id });
    } else {
      openErrorNotification(`Schedule with id=${id} is not found. Please select schedule from the list.`);
    }
  };

  update = () => {
    const { store } = this.props;
    const { scheduleStore } = store;

    return scheduleStore.updateItems();
  };

  render() {
    const { store, query } = this.props;
    const { expandedSchedulesKeys, scheduleIdToDelete, scheduleIdToEdit, scheduleIdToExport } = this.state;
    const { filters, errorData } = this.state;
    const { scheduleStore } = store;

    const columns = [
      {
        width: '10%',
        title: 'Type',
        dataIndex: 'type',
        render: this.renderType,
      },
      {
        width: '20%',
        title: 'Name',
        dataIndex: 'name',
      },
      {
        width: '20%',
        title: 'OnCall now',
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
        width: '10%',
        key: 'warning',
        render: this.renderWarning,
      },
      {
        width: '20%',
        key: 'action',
        render: this.renderActionButtons,
      },
    ];

    const schedules = scheduleStore.getSearchResult();

    const timezoneStr = moment.tz.guess();
    const offset = moment().tz(timezoneStr).format('Z');

    return (
      <PluginPage>
        <PageErrorHandlingWrapper
          errorData={errorData}
          objectName="schedule"
          pageName="schedules"
          itemNotFoundMessage={`Schedule with id=${query?.id} is not found. Please select schedule from the list.`}
        >
          {() => (
            <>
              <div className={cx('root')}>
                <div className={cx('title')}>
                  <HorizontalGroup align="flex-end">
                    <Text.Title level={3}>On-call Schedules</Text.Title>
                    <Text type="secondary">
                      Use this to distribute notifications among team members you specified in the "Notify Users from
                      on-call schedule" step in{' '}
                      <PluginLink query={{ page: 'integrations' }}>escalation chains</PluginLink>.
                    </Text>
                  </HorizontalGroup>
                </div>

                {!schedules || schedules.length ? (
                  <GTable
                    emptyText={schedules ? 'No schedules found' : 'Loading...'}
                    title={() => (
                      <div className={cx('header')}>
                        <HorizontalGroup className={cx('filters')} spacing="md">
                          <SchedulesFilters value={filters} onChange={this.handleChangeFilters} />
                          <Text type="secondary">
                            <Icon name="info-circle" /> Your timezone is {timezoneStr} UTC{offset}
                          </Text>
                        </HorizontalGroup>
                        <PluginLink
                          partial
                          query={{ id: 'new' }}
                          disabled={!store.isUserActionAllowed(UserAction.UpdateSchedules)}
                        >
                          <WithPermissionControl userAction={UserAction.UpdateSchedules}>
                            <Button variant="primary" icon="plus">
                              New schedule
                            </Button>
                          </WithPermissionControl>
                        </PluginLink>
                      </div>
                    )}
                    rowKey="id"
                    columns={columns}
                    data={schedules}
                    expandable={{
                      expandedRowRender: this.renderEvents,
                      expandRowByClick: true,
                      onExpand: this.onRowExpand,
                      expandedRowKeys: expandedSchedulesKeys,
                      onExpandedRowsChange: this.handleExpandedRowsChange,
                    }}
                  />
                ) : (
                  <Tutorial
                    step={TutorialStep.Schedules}
                    title={
                      <VerticalGroup align="center" spacing="lg">
                        <Text type="secondary">You haven’t added a schedule yet.</Text>
                        <PluginLink partial query={{ id: 'new' }}>
                          <Button icon="plus" variant="primary" size="lg">
                            Add team schedule for on-call rotation
                          </Button>
                        </PluginLink>
                      </VerticalGroup>
                    }
                  />
                )}
              </div>

              {scheduleIdToEdit && (
                <ScheduleForm
                  id={scheduleIdToEdit}
                  type={ScheduleType.Ical}
                  onUpdate={this.update}
                  onHide={() => {
                    this.setState({ scheduleIdToEdit: undefined });
                    getLocationSrv().update({ partial: true, query: { id: undefined } });
                  }}
                />
              )}

              {scheduleIdToDelete && (
                <ConfirmModal
                  isOpen
                  title="Are you sure to delete?"
                  confirmText="Delete"
                  dismissText="Cancel"
                  onConfirm={this.handleDelete}
                  body={null}
                  onDismiss={() => {
                    this.setState({ scheduleIdToDelete: undefined });
                  }}
                />
              )}

              {scheduleIdToExport && (
                <Modal
                  isOpen
                  title="Schedule export"
                  closeOnEscape
                  onDismiss={() => this.setState({ scheduleIdToExport: undefined })}
                >
                  <ScheduleICalSettings id={scheduleIdToExport} />
                </Modal>
              )}
            </>
          )}
        </PageErrorHandlingWrapper>
      </PluginPage>
    );
  }

  onRowExpand = (expanded: boolean, schedule: Schedule) => {
    if (expanded) {
      this.updateEventsFor(schedule.id);
    }
  };

  handleExpandedRowsChange = (expandedRows: string[]) => {
    this.setState({ expandedSchedulesKeys: expandedRows });
  };

  renderEvents = (schedule: Schedule) => {
    const { store } = this.props;
    const { scheduleStore } = store;
    const { scheduleToScheduleEvents } = scheduleStore;

    const events = scheduleToScheduleEvents[schedule.id];

    return events ? (
      events.length ? (
        <div className={cx('events')}>
          <Text.Title type="secondary" level={3}>
            Events
          </Text.Title>
          <ul className={cx('events-list')}>
            {(events || []).map((event) => (
              <li className={cx('events-list-item')}>
                <Event event={event} />
              </li>
            ))}
          </ul>
        </div>
      ) : (
        this.renderInstruction()
      )
    ) : (
      <LoadingPlaceholder text="Loading events..." />
    );
  };

  renderInstruction = () => {
    const { store } = this.props;
    const { userStore } = store;

    return (
      <div className={cx('instructions')}>
        <Text type="secondary">
          There are no active slots here. To add an event, enter a username, for example “
          {userStore.currentUser?.username}“, and click the “Reload” button. OnCall will download this calendar and set
          up an on-call schedule based on event names. OnCall will refresh the calendar every 10 minutes after the
          intial setup.
        </Text>
        <img style={{ width: '400px' }} src={instructionsImage} />
      </div>
    );
  };

  handleChangeFilters = (filters: SchedulesFiltersType) => {
    this.setState({ filters }, () => {
      const { filters, expandedSchedulesKeys } = this.state;

      if (!filters.selectedDate) {
        return;
      }

      expandedSchedulesKeys.forEach((id) => this.updateEventsFor(id));
    });
  };

  renderChannelName = (value: Schedule) => {
    return getSlackChannelName(value.slack_channel) || '-';
  };

  renderUserGroup = (value: Schedule) => {
    return value.user_group?.handle || '-';
  };

  renderOncallNow = (item: Schedule, index: number) => {
    if (item.on_call_now?.length > 0) {
      return item.on_call_now.map((user, index) => {
        return (
          <PluginLink key={user.pk} query={{ page: 'users', id: user.pk }}>
            <div>
              <Avatar size="small" src={user.avatar} />
              <Text type="secondary"> {user.username}</Text>
            </div>
          </PluginLink>
        );
      });
    }
    return null;
  };

  renderType = (value: number) => {
    type tTypeToVerbal = {
      [key: number]: string;
    };
    const typeToVerbal: tTypeToVerbal = { 0: 'API/Terraform', 1: 'Ical', 2: 'Web' };
    return typeToVerbal[value];
  };

  renderWarning = (item: Schedule) => {
    if (item.warnings.length > 0) {
      const tooltipContent = (
        <div>
          {item.warnings.map((warning: string) => (
            <p>{warning}</p>
          ))}
        </div>
      );
      return (
        <Tooltip placement="top" content={tooltipContent}>
          <Icon style={{ color: PENDING_COLOR }} name="exclamation-triangle" />
        </Tooltip>
      );
    }

    return null;
  };

  renderActionButtons = (record: Schedule) => {
    return (
      <HorizontalGroup justify="flex-end">
        <WithPermissionControl key="edit" userAction={UserAction.UpdateSchedules}>
          <Button
            onClick={(event) => {
              event.stopPropagation();

              this.setState({ scheduleIdToEdit: record.id });

              getLocationSrv().update({ partial: true, query: { id: record.id } });
            }}
            fill="text"
          >
            Edit
          </Button>
        </WithPermissionControl>
        <WithPermissionControl key="reload" userAction={UserAction.UpdateSchedules}>
          <Button onClick={this.getReloadScheduleClickHandler(record.id)} fill="text">
            Reload
          </Button>
        </WithPermissionControl>
        <WithPermissionControl key="export" userAction={UserAction.UpdateSchedules}>
          <Button onClick={this.getExportScheduleClickHandler(record.id)} fill="text">
            Export
          </Button>
        </WithPermissionControl>
        <WithPermissionControl key="delete" userAction={UserAction.UpdateSchedules}>
          <Button onClick={this.getDeleteScheduleClickHandler(record.id)} fill="text" variant="destructive">
            Delete
          </Button>
        </WithPermissionControl>
      </HorizontalGroup>
    );
  };

  updateEventsFor = async (scheduleId: Schedule['id'], withEmpty = true, with_gap = true) => {
    const { store } = this.props;

    const { scheduleStore } = store;
    const {
      filters: { selectedDate },
    } = this.state;

    store.scheduleStore.scheduleToScheduleEvents = omit(store.scheduleStore.scheduleToScheduleEvents, [scheduleId]);

    this.forceUpdate();

    await scheduleStore.updateScheduleEvents(scheduleId, withEmpty, with_gap, selectedDate, moment.tz.guess());

    this.forceUpdate();
  };

  getReloadScheduleClickHandler = (scheduleId: Schedule['id']) => {
    const { store } = this.props;

    const { scheduleStore } = store;

    return async (event: SyntheticEvent) => {
      event.stopPropagation();

      await scheduleStore.reloadIcal(scheduleId);

      scheduleStore.updateItem(scheduleId);
      this.updateEventsFor(scheduleId);
    };
  };

  getDeleteScheduleClickHandler = (scheduleId: Schedule['id']) => {
    return (event: SyntheticEvent) => {
      event.stopPropagation();
      this.setState({ scheduleIdToDelete: scheduleId });
    };
  };

  getExportScheduleClickHandler = (scheduleId: Schedule['id']) => {
    return (event: SyntheticEvent) => {
      event.stopPropagation();
      this.setState({ scheduleIdToExport: scheduleId });
    };
  };

  handleDelete = async () => {
    const { scheduleIdToDelete } = this.state;
    const { store } = this.props;

    this.setState({ scheduleIdToDelete: undefined });

    const { scheduleStore } = store;

    await scheduleStore.delete(scheduleIdToDelete);

    this.update();
  };
}

interface EventProps {
  event: ScheduleEvent;
}

const Event = ({ event }: EventProps) => {
  const dates = getDatesString(event.start, event.end, event.all_day);

  return (
    <>
      {!event.is_gap ? (
        <HorizontalGroup align="flex-start" spacing="sm">
          <div className={cx('priority-icon')}>
            <Text wrap type="secondary">{`L${event.priority_level || '0'}`}</Text>
          </div>
          <VerticalGroup>
            <div>
              {!event.is_empty ? (
                event.users.map((user: any, index: number) => (
                  <span key={user.pk}>
                    {index ? ', ' : ''}
                    <PluginLink query={{ page: 'users', id: user.pk }}>{user.display_name}</PluginLink>
                  </span>
                ))
              ) : (
                <HorizontalGroup spacing="sm">
                  <Icon style={{ color: PENDING_COLOR }} name="exclamation-triangle" />
                  <Text type="secondary">Empty shift</Text>
                  {event.missing_users[0] && (
                    <Text type="secondary">
                      (check if {event.missing_users[0].includes(',') ? 'some of these users -' : 'user -'}{' '}
                      <Text type="secondary">"{event.missing_users[0]}"</Text>{' '}
                      {event.missing_users[0].includes(',') ? 'are' : 'is'} existing in OnCall or{' '}
                      {event.missing_users[0].includes(',') ? 'have' : 'has'} Viewer role)
                    </Text>
                  )}
                </HorizontalGroup>
              )}
              {event.source && <span> — source: {event.source}</span>}
            </div>
            <div>
              <Text type="secondary"> {dates}</Text>
            </div>
          </VerticalGroup>
        </HorizontalGroup>
      ) : (
        <div className={cx('gap-between-shifts')}>
          <Icon name="exclamation-triangle" className={cx('gap-between-shifts-icon')} />
          <Text> Gap! Nobody On-Call...</Text>
        </div>
      )}
    </>
  );
};

export default withMobXProviderContext(SchedulesPage);
