import React from 'react';

import { AppRootProps } from '@grafana/data';
import { getLocationSrv } from '@grafana/runtime';
import { Button, HorizontalGroup, VerticalGroup, IconButton, ToolbarButton, Icon } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';

import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import UserTimezoneSelect from 'components/UserTimezoneSelect/UserTimezoneSelect';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import Rotations from 'containers/Rotations/Rotations';
import ScheduleFinal from 'containers/Rotations/ScheduleFinal';
import ScheduleOverrides from 'containers/Rotations/ScheduleOverrides';
import ScheduleForm from 'containers/ScheduleForm/ScheduleForm';
import UsersTimezones from 'containers/UsersTimezones/UsersTimezones';
import { Shift } from 'models/schedule/schedule.types';
import { Timezone } from 'models/timezone/timezone.types';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';

import { getStartOfWeek } from './Schedule.helpers';

import styles from './Schedule.module.css';

const cx = cn.bind(styles);

interface SchedulePageProps extends AppRootProps, WithStoreProps {}

interface SchedulePageState {
  startMoment: dayjs.Dayjs;
  schedulePeriodType: string;
  renderType: string;
  shiftIdToShowRotationForm?: Shift['id'];
  shiftIdToShowOverridesForm?: Shift['id'];
  isLoading: boolean;
  showEditForm: boolean;
}

@observer
class SchedulePage extends React.Component<SchedulePageProps, SchedulePageState> {
  constructor(props: SchedulePageProps) {
    super(props);

    const { currentTimezone } = this.props.store;
    this.state = {
      startMoment: getStartOfWeek(currentTimezone),
      schedulePeriodType: 'week',
      renderType: 'timeline',
      shiftIdToShowRotationForm: undefined,
      shiftIdToShowOverridesForm: undefined,
      isLoading: true,
      showEditForm: false,
    };
  }

  async componentDidMount() {
    const {
      query: { id },
      store: { scheduleStore, userStore },
    } = this.props;

    userStore.updateItems();

    scheduleStore.updateFrequencyOptions();
    scheduleStore.updateDaysOptions();
    await scheduleStore.updateOncallShifts(id); // TODO we should know shifts to render Rotations
    await this.updateEvents();

    this.setState({ isLoading: false });
  }

  componentWillUnmount() {
    const { scheduleStore } = this.props.store;

    scheduleStore.clearPreview();
  }

  render() {
    const {
      query: { id: scheduleId },
      store: { scheduleStore, currentTimezone, userStore },
    } = this.props;
    const { startMoment, shiftIdToShowRotationForm, shiftIdToShowOverridesForm, showEditForm } = this.state;

    const users = userStore.getSearchResult().results;
    const schedule = scheduleStore.items[scheduleId];

    return (
      <>
        <div className={cx('root')}>
          <VerticalGroup spacing="lg">
            <div className={cx('header')}>
              <HorizontalGroup justify="space-between">
                <HorizontalGroup>
                  <PluginLink query={{ page: 'schedules-new' }}>
                    <IconButton style={{ marginTop: '5px' }} name="arrow-left" size="xl" />
                  </PluginLink>
                  <Text.Title editable editModalTitle="Schedule name" level={2} onTextChange={this.handleNameChange}>
                    {schedule?.name}
                  </Text.Title>
                </HorizontalGroup>
                <HorizontalGroup spacing="lg">
                  {users && (
                    <HorizontalGroup>
                      <Text type="secondary">Current timezone:</Text>
                      <UserTimezoneSelect value={currentTimezone} users={users} onChange={this.handleTimezoneChange} />
                    </HorizontalGroup>
                  )}
                  <HorizontalGroup>
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
                  scheduleStore.relatedUsers[scheduleId] ? Object.keys(scheduleStore.relatedUsers[scheduleId]) : []
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
                </HorizontalGroup>
              </div>
              <ScheduleFinal
                scheduleId={scheduleId}
                currentTimezone={currentTimezone}
                startMoment={startMoment}
                onClick={this.handleShowForm}
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
                disabled={shiftIdToShowRotationForm || shiftIdToShowOverridesForm}
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
                disabled={shiftIdToShowRotationForm || shiftIdToShowOverridesForm}
              />
            </div>
          </VerticalGroup>
        </div>
        {showEditForm && (
          <ScheduleForm
            id={schedule.id}
            onUpdate={this.update}
            onHide={() => {
              this.setState({ showEditForm: false });
            }}
          />
        )}
      </>
    );
  }

  update = () => {
    const {
      store: { scheduleStore },
      query: { id: scheduleId },
    } = this.props;
    return scheduleStore.updateItem(scheduleId);
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
    const { shiftIdToShowRotationForm, shiftIdToShowOverridesForm } = this.state;

    if (shiftId && (shiftIdToShowRotationForm || shiftIdToShowOverridesForm)) {
      return;
    }

    this.setState({ shiftIdToShowRotationForm: shiftId });
  };

  handleShowOverridesForm = (shiftId: Shift['id'] | 'new') => {
    const { shiftIdToShowRotationForm, shiftIdToShowOverridesForm } = this.state;

    if (shiftId && (shiftIdToShowRotationForm || shiftIdToShowOverridesForm)) {
      return;
    }

    this.setState({ shiftIdToShowOverridesForm: shiftId });
  };

  handleNameChange = (value: string) => {
    const {
      store: { scheduleStore },
      query: { id: scheduleId },
    } = this.props;
    const schedule = scheduleStore.items[scheduleId];

    scheduleStore
      .update(scheduleId, { type: schedule.type, name: value })
      .then(() => scheduleStore.updateItem(scheduleId));
  };

  updateEvents = () => {
    const {
      store: { scheduleStore },
      query: { id: scheduleId },
    } = this.props;

    const { startMoment } = this.state;

    scheduleStore.updateItem(scheduleId); // to refresh current oncall users
    scheduleStore.updateRelatedUsers(scheduleId); // to refresh related users

    return Promise.all([
      scheduleStore.updateEvents(scheduleId, startMoment, 'rotation'),
      scheduleStore.updateEvents(scheduleId, startMoment, 'override'),
      scheduleStore.updateEvents(scheduleId, startMoment, 'final'),
    ]);
  };

  handleCreateRotation = () => {
    const { scheduleStore } = this.props.store;

    this.updateEvents().then(() => {
      scheduleStore.clearPreview();
    });
  };

  handleCreateOverride = () => {
    const { scheduleStore } = this.props.store;

    this.updateEvents().then(() => {
      scheduleStore.clearPreview();
    });
  };

  handleUpdateRotation = () => {
    const { scheduleStore } = this.props.store;

    this.updateEvents().then(() => {
      scheduleStore.clearPreview();
    });
  };

  handleDeleteRotation = () => {
    const { scheduleStore } = this.props.store;

    this.updateEvents().then(() => {
      scheduleStore.clearPreview();
    });
  };

  handleDeleteOverride = () => {
    const { scheduleStore } = this.props.store;

    this.updateEvents().then(() => {
      scheduleStore.clearPreview();
    });
  };

  handleUpdateOverride = () => {
    const { scheduleStore } = this.props.store;

    this.updateEvents().then(() => {
      scheduleStore.clearPreview();
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
    const { currentTimezone } = this.props.store;
    this.setState({ startMoment: getStartOfWeek(currentTimezone) }, this.handleDateRangeUpdate);
  };

  handleLeftClick = () => {
    const { startMoment } = this.state;
    this.setState({ startMoment: startMoment.add(-7, 'day') }, this.handleDateRangeUpdate);
  };

  handleRightClick = () => {
    const { startMoment } = this.state;
    this.setState({ startMoment: startMoment.add(7, 'day') }, this.handleDateRangeUpdate);
  };

  handleDelete = () => {
    const {
      store: { scheduleStore },
      query: { id: scheduleId },
    } = this.props;

    scheduleStore.delete(scheduleId).then(() => {
      getLocationSrv().update({ query: { page: 'schedules-new' } });
    });
  };
}

export default withMobXProviderContext(SchedulePage);
