import React from 'react';

import { Button, HorizontalGroup, VerticalGroup, IconButton, ToolbarButton, Icon, Modal } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';
import { RouteComponentProps, withRouter } from 'react-router-dom';

import PageErrorHandlingWrapper, { PageBaseState } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper';
import {
  getWrongTeamResponseInfo,
  initErrorDataState,
} from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper.helpers';
import PluginLink from 'components/PluginLink/PluginLink';
import ScheduleFilters from 'components/ScheduleFilters/ScheduleFilters';
import { ScheduleFiltersType } from 'components/ScheduleFilters/ScheduleFilters.types';
import ScheduleQuality from 'components/ScheduleQuality/ScheduleQuality';
import Text from 'components/Text/Text';
import UserTimezoneSelect from 'components/UserTimezoneSelect/UserTimezoneSelect';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import ShiftSwapForm from 'containers/RotationForm/ShiftSwapForm';
import Rotations from 'containers/Rotations/Rotations';
import ScheduleFinal from 'containers/Rotations/ScheduleFinal';
import ScheduleOverrides from 'containers/Rotations/ScheduleOverrides';
import ScheduleForm from 'containers/ScheduleForm/ScheduleForm';
import ScheduleICalSettings from 'containers/ScheduleIcalLink/ScheduleIcalLink';
import UsersTimezones from 'containers/UsersTimezones/UsersTimezones';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { Event, Schedule, ScheduleType, Shift, ShiftSwap } from 'models/schedule/schedule.types';
import { Timezone } from 'models/timezone/timezone.types';
import { PageProps, WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import { isUserActionAllowed, UserActions } from 'utils/authorization';
import { PLUGIN_ROOT } from 'utils/consts';

import { getStartOfWeek } from './Schedule.helpers';

import styles from './Schedule.module.css';

const cx = cn.bind(styles);

interface SchedulePageProps extends PageProps, WithStoreProps, RouteComponentProps<{ id: string }> {}

interface SchedulePageState extends PageBaseState {
  startMoment: dayjs.Dayjs;
  schedulePeriodType: string;
  renderType: string;
  shiftIdToShowRotationForm?: Shift['id'];
  shiftIdToShowOverridesForm?: Shift['id'];
  shiftStartToShowOverrideForm?: dayjs.Dayjs;
  shiftEndToShowOverrideForm?: dayjs.Dayjs;
  isLoading: boolean;
  showEditForm: boolean;
  showScheduleICalSettings: boolean;
  lastUpdated: number;
  filters: ScheduleFiltersType;
  shiftSwapIdToShowForm?: ShiftSwap['id'] | 'new';
  shiftSwapParamsToShowForm?: Partial<ShiftSwap>;
}

@observer
class SchedulePage extends React.Component<SchedulePageProps, SchedulePageState> {
  highlightMyShiftsWasToggled = false;

  constructor(props: SchedulePageProps) {
    super(props);

    const { store } = this.props;
    this.state = {
      startMoment: getStartOfWeek(store.currentTimezone),
      schedulePeriodType: 'week',
      renderType: 'timeline',
      shiftIdToShowRotationForm: undefined,
      shiftIdToShowOverridesForm: undefined,
      isLoading: true,
      showEditForm: false,
      showScheduleICalSettings: false,
      errorData: initErrorDataState(),
      lastUpdated: 0,
      filters: { users: [] },
    };
  }

  async componentDidMount() {
    const {
      store,
      match: {
        params: { id },
      },
    } = this.props;

    store.userStore.updateItems();

    store.scheduleStore.updateFrequencyOptions();
    store.scheduleStore.updateDaysOptions();
    await store.scheduleStore.updateOncallShifts(id); // TODO we should know shifts to render Rotations
    await this.updateEvents();

    this.setState({ isLoading: false });
  }

  componentWillUnmount() {
    const { store } = this.props;

    store.scheduleStore.clearPreview();
  }

  render() {
    const {
      store,
      query,
      match: {
        params: { id: scheduleId },
      },
    } = this.props;

    const {
      startMoment,

      shiftIdToShowRotationForm,
      shiftIdToShowOverridesForm,
      showEditForm,
      showScheduleICalSettings,
      errorData,
      shiftStartToShowOverrideForm,
      shiftEndToShowOverrideForm,
      filters,
      shiftSwapIdToShowForm,
      shiftSwapParamsToShowForm,
    } = this.state;

    const { isNotFoundError } = errorData;

    const { scheduleStore, currentTimezone } = store;

    const users = store.userStore.getSearchResult().results;
    const schedule = scheduleStore.items[scheduleId];

    const disabledRotationForm =
      !isUserActionAllowed(UserActions.SchedulesWrite) ||
      schedule?.type !== ScheduleType.API ||
      !!shiftIdToShowRotationForm ||
      shiftIdToShowOverridesForm;

    const disabledOverrideForm =
      !isUserActionAllowed(UserActions.SchedulesWrite) ||
      !schedule?.enable_web_overrides ||
      !!shiftIdToShowOverridesForm ||
      shiftIdToShowRotationForm;

    return (
      <PageErrorHandlingWrapper errorData={errorData} objectName="schedule" pageName="schedules">
        {() => (
          <>
            <div className={cx('root')}>
              {isNotFoundError ? (
                <div className={cx('not-found')}>
                  <VerticalGroup spacing="lg" align="center">
                    <Text.Title level={1}>404</Text.Title>
                    <Text.Title level={4}>Schedule not found</Text.Title>
                    <PluginLink query={{ page: 'schedules', ...query }}>
                      <Button variant="secondary" icon="arrow-left" size="md">
                        Go to Schedules page
                      </Button>
                    </PluginLink>
                  </VerticalGroup>
                </div>
              ) : (
                <VerticalGroup spacing="lg">
                  <div className={cx('header')}>
                    <HorizontalGroup justify="space-between">
                      <div className={cx('title')}>
                        <PluginLink query={{ page: 'schedules', ...query }}>
                          <IconButton style={{ marginTop: '5px' }} name="arrow-left" size="xl" />
                        </PluginLink>
                        <Text.Title
                          editable={false}
                          editModalTitle="Schedule name"
                          level={2}
                          onTextChange={this.handleNameChange}
                        >
                          {schedule?.name}
                        </Text.Title>
                        {schedule && <ScheduleQuality schedule={schedule} lastUpdated={this.state.lastUpdated} />}
                      </div>
                      <HorizontalGroup spacing="lg">
                        {users && (
                          <HorizontalGroup>
                            <Text type="secondary">Current timezone:</Text>
                            <UserTimezoneSelect
                              value={currentTimezone}
                              users={users}
                              onChange={this.handleTimezoneChange}
                            />
                          </HorizontalGroup>
                        )}
                        <HorizontalGroup>
                          <HorizontalGroup>
                            <HorizontalGroup>
                              <Button variant="secondary" onClick={this.handleExportClick()}>
                                Export
                              </Button>
                            </HorizontalGroup>

                            {(schedule?.type === ScheduleType.Ical || schedule?.type === ScheduleType.Calendar) && (
                              <WithPermissionControlTooltip userAction={UserActions.SchedulesWrite}>
                                <Button variant="secondary" onClick={this.handleReloadClick(scheduleId)}>
                                  Reload
                                </Button>
                              </WithPermissionControlTooltip>
                            )}
                          </HorizontalGroup>
                          <ToolbarButton
                            icon="cog"
                            tooltip="Settings"
                            onClick={() => {
                              this.setState({ showEditForm: true });
                            }}
                          />
                          <WithConfirm>
                            <ToolbarButton icon="trash-alt" tooltip="Delete" onClick={this.handleDelete} />
                          </WithConfirm>
                        </HorizontalGroup>
                      </HorizontalGroup>
                    </HorizontalGroup>
                  </div>
                  <div className={cx('users-timezones')}>
                    <UsersTimezones
                      scheduleId={scheduleId}
                      startMoment={startMoment}
                      onCallNow={schedule?.on_call_now || []}
                      userIds={
                        scheduleStore.relatedUsers[scheduleId]
                          ? Object.keys(scheduleStore.relatedUsers[scheduleId])
                          : []
                      }
                      tz={currentTimezone}
                      onTzChange={this.handleTimezoneChange}
                    />
                  </div>

                  <div className={cx('rotations')}>
                    <div className={cx('controls')}>
                      <HorizontalGroup justify="space-between">
                        <HorizontalGroup>
                          <Button variant="secondary" onClick={this.handleTodayClick}>
                            Today
                          </Button>
                          <HorizontalGroup spacing="xs">
                            <Button variant="secondary" onClick={this.handleLeftClick}>
                              <Icon name="angle-left" />
                            </Button>
                            <Button variant="secondary" onClick={this.handleRightClick}>
                              <Icon name="angle-right" />
                            </Button>
                          </HorizontalGroup>
                          <Text.Title style={{ marginLeft: '8px' }} level={4} type="primary">
                            {startMoment.format('DD MMM')} - {startMoment.add(6, 'day').format('DD MMM')}
                          </Text.Title>
                        </HorizontalGroup>
                        <ScheduleFilters
                          value={filters}
                          onChange={(value) => this.setState({ filters: value })}
                          currentUserPk={store.userStore.currentUserPk}
                        />
                      </HorizontalGroup>
                    </div>
                    <ScheduleFinal
                      scheduleId={scheduleId}
                      currentTimezone={currentTimezone}
                      startMoment={startMoment}
                      disabled={disabledRotationForm}
                      onShowOverrideForm={this.handleShowOverridesForm}
                      filters={filters}
                      onShowShiftSwapForm={this.handleShowShiftSwapForm}
                      onSlotClick={
                        shiftSwapIdToShowForm
                          ? this.adjustShiftSwapForm
                          : (event: Event) => {
                              this.handleShowForm(event.shift.pk);
                            }
                      }
                    />
                    <Rotations
                      scheduleId={scheduleId}
                      currentTimezone={currentTimezone}
                      startMoment={startMoment}
                      onCreate={this.handleCreateRotation}
                      onUpdate={this.handleUpdateRotation}
                      onDelete={this.handleDeleteRotation}
                      shiftIdToShowRotationForm={shiftIdToShowRotationForm}
                      onShowRotationForm={this.handleShowRotationForm}
                      onShowOverrideForm={this.handleShowOverridesForm}
                      disabled={disabledRotationForm}
                      filters={filters}
                      onShowShiftSwapForm={this.handleShowShiftSwapForm}
                      onSlotClick={shiftSwapIdToShowForm ? this.adjustShiftSwapForm : undefined}
                    />
                    <ScheduleOverrides
                      scheduleId={scheduleId}
                      currentTimezone={currentTimezone}
                      startMoment={startMoment}
                      onCreate={this.handleCreateOverride}
                      onUpdate={this.handleUpdateOverride}
                      onDelete={this.handleDeleteOverride}
                      shiftIdToShowRotationForm={shiftIdToShowOverridesForm}
                      onShowRotationForm={this.handleShowOverridesForm}
                      disabled={disabledOverrideForm}
                      shiftStartToShowOverrideForm={shiftStartToShowOverrideForm}
                      shiftEndToShowOverrideForm={shiftEndToShowOverrideForm}
                      filters={filters}
                    />
                  </div>
                </VerticalGroup>
              )}
            </div>
            {showEditForm && schedule && (
              <ScheduleForm
                id={scheduleId}
                onSubmit={this.update}
                onHide={() => {
                  this.setState({ showEditForm: false });
                }}
              />
            )}
            {showScheduleICalSettings && (
              <Modal
                isOpen
                title="Schedule export"
                closeOnEscape
                onDismiss={() => this.setState({ showScheduleICalSettings: false })}
              >
                <ScheduleICalSettings id={scheduleId} />
              </Modal>
            )}
            {shiftSwapIdToShowForm && (
              <ShiftSwapForm
                id={shiftSwapIdToShowForm}
                scheduleId={scheduleId}
                currentTimezone={currentTimezone}
                params={shiftSwapParamsToShowForm}
                onHide={this.handleHideShiftSwapForm}
                onUpdate={this.updateEvents}
              />
            )}
          </>
        )}
      </PageErrorHandlingWrapper>
    );
  }

  update = () => {
    const {
      store,
      match: {
        params: { id: scheduleId },
      },
    } = this.props;
    const { scheduleStore } = store;

    return scheduleStore.loadItem(scheduleId);
  };

  handleShowForm = async (shiftId: Shift['id'] | 'new') => {
    const {
      store: { scheduleStore },
    } = this.props;

    const shift = await scheduleStore.updateOncallShift(shiftId);

    if (shift.type === 2) {
      this.handleShowRotationForm(shiftId);
    } else if (shift.type === 3) {
      this.handleShowOverridesForm(shiftId);
    }
  };

  handleShowRotationForm = (shiftId: Shift['id'] | 'new') => {
    this.setState({ shiftIdToShowRotationForm: shiftId });
  };

  handleShowOverridesForm = (shiftId: Shift['id'] | 'new', shiftStart?: dayjs.Dayjs, shiftEnd?: dayjs.Dayjs) => {
    this.setState({
      shiftIdToShowOverridesForm: shiftId,
      shiftStartToShowOverrideForm: shiftStart,
      shiftEndToShowOverrideForm: shiftEnd,
    });
  };

  handleNameChange = (value: string) => {
    const {
      store,
      match: {
        params: { id: scheduleId },
      },
    } = this.props;

    const schedule = store.scheduleStore.items[scheduleId];

    store.scheduleStore
      .update(scheduleId, { type: schedule.type, name: value })
      .then(() => store.scheduleStore.loadItem(scheduleId));
  };

  updateEvents = () => {
    const {
      store,
      match: {
        params: { id: scheduleId },
      },
    } = this.props;

    const { startMoment } = this.state;

    this.setState((prevState) => ({
      // this will update schedule score
      lastUpdated: prevState.lastUpdated + 1,
    }));

    store.scheduleStore
      .loadItem(scheduleId) // to refresh current oncall users
      .catch((error) => this.setState({ errorData: { ...getWrongTeamResponseInfo(error) } }));
    store.scheduleStore.updateRelatedUsers(scheduleId); // to refresh related users

    return Promise.all([
      store.scheduleStore.updateEvents(scheduleId, startMoment, 'rotation'),
      store.scheduleStore.updateEvents(scheduleId, startMoment, 'override'),
      store.scheduleStore.updateEvents(scheduleId, startMoment, 'final'),
    ]);
  };

  handleCreateRotation = () => {
    const { store } = this.props;

    this.updateEvents().then(() => {
      store.scheduleStore.clearPreview();
    });
  };

  handleCreateOverride = () => {
    const { store } = this.props;

    this.updateEvents().then(() => {
      store.scheduleStore.clearPreview();
    });
  };

  handleUpdateRotation = () => {
    const { store } = this.props;

    this.updateEvents().then(() => {
      store.scheduleStore.clearPreview();
    });
  };

  handleDeleteRotation = () => {
    const { store } = this.props;

    this.updateEvents().then(() => {
      store.scheduleStore.clearPreview();
    });
  };

  handleDeleteOverride = () => {
    const { store } = this.props;

    this.updateEvents().then(() => {
      store.scheduleStore.clearPreview();
    });
  };

  handleUpdateOverride = () => {
    const { store } = this.props;

    this.updateEvents().then(() => {
      store.scheduleStore.clearPreview();
    });
  };

  handleTimezoneChange = (value: Timezone) => {
    const { store } = this.props;

    const oldTimezone = store.currentTimezone;

    this.setState((oldState) => {
      const wDiff = oldState.startMoment.diff(getStartOfWeek(oldTimezone), 'weeks');

      return { ...oldState, startMoment: getStartOfWeek(value).add(wDiff, 'weeks') };
    }, this.updateEvents);

    store.currentTimezone = value;
  };

  handleShedulePeriodTypeChange = (value: string) => {
    this.setState({ schedulePeriodType: value });
  };

  handleRenderTypeChange = (value: string) => {
    this.setState({ renderType: value });
  };

  handleDateRangeUpdate = async () => {
    await this.updateEvents();
    this.forceUpdate();
  };

  handleTodayClick = () => {
    const { store } = this.props;
    this.setState({ startMoment: getStartOfWeek(store.currentTimezone) }, this.handleDateRangeUpdate);
  };

  handleLeftClick = () => {
    const { startMoment } = this.state;
    this.setState({ startMoment: startMoment.add(-7, 'day') }, this.handleDateRangeUpdate);
  };

  handleRightClick = () => {
    const { startMoment } = this.state;
    this.setState({ startMoment: startMoment.add(7, 'day') }, this.handleDateRangeUpdate);
  };

  handleExportClick = () => {
    return () => {
      this.setState({ showScheduleICalSettings: true });
    };
  };

  handleReloadClick = (scheduleId: Schedule['id']) => {
    const { store } = this.props;

    const { scheduleStore } = store;

    return async () => {
      await scheduleStore.reloadIcal(scheduleId);

      store.scheduleStore.updateOncallShifts(scheduleId);
      this.updateEvents();
    };
  };

  handleDelete = () => {
    const {
      store,
      match: {
        params: { id },
      },
      history,
    } = this.props;

    store.scheduleStore.delete(id).then(() => history.replace(`${PLUGIN_ROOT}/schedules`));
  };

  handleShowShiftSwapForm = (id: ShiftSwap['id'], params: Partial<ShiftSwap>) => {
    const { filters } = this.state;

    const {
      store: { userStore },
    } = this.props;

    if (!filters.users.includes(userStore.currentUserPk)) {
      this.setState({ filters: { ...filters, users: [...this.state.filters.users, userStore.currentUserPk] } });
      this.highlightMyShiftsWasToggled = true;
    }

    this.setState({ shiftSwapIdToShowForm: id, shiftSwapParamsToShowForm: params });
  };

  handleHideShiftSwapForm = () => {
    const { filters } = this.state;

    const {
      store: { userStore },
    } = this.props;

    if (this.highlightMyShiftsWasToggled) {
      this.highlightMyShiftsWasToggled = false;
      const index = filters.users.indexOf(userStore.currentUserPk);

      if (index > -1) {
        const newUsers = [...filters.users];
        newUsers.splice(index, 1);

        this.setState({ filters: { ...filters, users: newUsers } });
      }
    }
    this.setState({ shiftSwapIdToShowForm: undefined, shiftSwapParamsToShowForm: undefined });
  };

  adjustShiftSwapForm = (event: Event) => {
    this.setState({
      shiftSwapParamsToShowForm: {
        ...this.state.shiftSwapParamsToShowForm,
        swap_start: event.start,
        swap_end: event.end,
      },
    });
  };
}

export default withRouter(withMobXProviderContext(SchedulePage));
