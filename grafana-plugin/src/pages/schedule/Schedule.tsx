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
}

const INITIAL_TIMEZONE = 'UTC'; // todo check why doesn't work

@observer
class SchedulePage extends React.Component<SchedulePageProps, SchedulePageState> {
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
    };
  }

  async componentDidMount() {
    const { store } = this.props;
    const {
      query: { id },
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
      query: { id: scheduleId },
      store,
    } = this.props;
    const { startMoment, shiftIdToShowRotationForm, shiftIdToShowOverridesForm } = this.state;
    const { scheduleStore, currentTimezone } = store;

    const users = store.userStore.getSearchResult().results;
    const schedule = scheduleStore.items[scheduleId];

    return (
      <div className={cx('root')}>
        <VerticalGroup spacing="lg">
          <div className={cx('header')}>
            <HorizontalGroup justify="space-between">
              <HorizontalGroup>
                <PluginLink query={{ page: 'schedules-new' }}>
                  <IconButton style={{ marginTop: '5px' }} name="arrow-left" size="xxl" />
                </PluginLink>
                <Text.Title editable editModalTitle="Schedule name" level={2} onTextChange={this.handleNameChange}>
                  {schedule?.name}
                </Text.Title>
              </HorizontalGroup>
              <HorizontalGroup>
                {users && (
                  <HorizontalGroup>
                    <Text type="secondary">Current timezone:</Text>
                    <UserTimezoneSelect value={currentTimezone} users={users} onChange={this.handleTimezoneChange} />
                  </HorizontalGroup>
                )}
                <WithConfirm>
                  <ToolbarButton icon="trash-alt" tooltip="Delete" onClick={this.handleDelete} />
                </WithConfirm>
              </HorizontalGroup>
            </HorizontalGroup>
          </div>
          <Text className={cx('desc')} size="small" type="secondary">
            On-call Schedules. Use this to distribute notifications among team members you specified in the "Notify
            Users from on-call schedule" step in escalation chains.
          </Text>
          <div className={cx('users-timezones')}>
            <UsersTimezones
              onCallNow={schedule?.on_call_now || []}
              userIds={
                scheduleStore.relatedUsers[scheduleId] ? Object.keys(scheduleStore.relatedUsers[scheduleId]) : []
              }
              tz={currentTimezone}
              startMoment={this.state.startMoment}
              onTzChange={this.handleTimezoneChange}
              scheduleId={scheduleId}
            />
          </div>
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
          <div className={cx('rotations')}>
            <ScheduleFinal
              currentTimezone={currentTimezone}
              startMoment={startMoment}
              onClick={this.handleShowForm}
              scheduleId={scheduleId}
            />
            <Rotations
              currentTimezone={currentTimezone}
              startMoment={startMoment}
              onCreate={this.handleCreateRotation}
              onUpdate={this.handleUpdateRotation}
              onDelete={this.handleDeleteRotation}
              shiftIdToShowRotationForm={shiftIdToShowRotationForm}
              onShowRotationForm={this.handleShowRotationForm}
              scheduleId={scheduleId}
            />
            <ScheduleOverrides
              currentTimezone={currentTimezone}
              startMoment={startMoment}
              onCreate={this.handleCreateOverride}
              onUpdate={this.handleUpdateOverride}
              onDelete={this.handleDeleteOverride}
              shiftIdToShowRotationForm={shiftIdToShowOverridesForm}
              onShowRotationForm={this.handleShowOverridesForm}
              scheduleId={scheduleId}
            />
          </div>
        </VerticalGroup>
      </div>
    );
  }

  handleShowForm = async (shiftId: Shift['id'] | 'new') => {
    const {
      store: { scheduleStore },
    } = this.props;

    const shift = await scheduleStore.updateOncallShift(shiftId);

    if (shift.type === 2) {
      this.setState({ shiftIdToShowRotationForm: shiftId });
    } else if (shift.type === 3) {
      this.setState({ shiftIdToShowOverridesForm: shiftId });
    }
  };

  handleShowRotationForm = (shiftId: Shift['id'] | 'new') => {
    this.setState({ shiftIdToShowRotationForm: shiftId });
  };

  handleShowOverridesForm = (shiftId: Shift['id'] | 'new') => {
    this.setState({ shiftIdToShowOverridesForm: shiftId });
  };

  handleNameChange = (value: string) => {
    const { store, query } = this.props;
    const { id: scheduleId } = query;

    const schedule = store.scheduleStore.items[scheduleId];

    store.scheduleStore
      .update(scheduleId, { type: schedule.type, name: value })
      .then(() => store.scheduleStore.updateItem(scheduleId));
  };

  updateEvents = () => {
    const {
      store,
      query: { id: scheduleId },
    } = this.props;

    const { startMoment } = this.state;

    store.scheduleStore.updateItem(scheduleId); // to refresh current oncall users
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

  handleDelete = () => {
    const {
      store,
      query: { id: scheduleId },
    } = this.props;

    store.scheduleStore.delete(scheduleId).then(() => {
      getLocationSrv().update({ query: { page: 'schedules-new' } });
    });
  };
}

export default withMobXProviderContext(SchedulePage);
