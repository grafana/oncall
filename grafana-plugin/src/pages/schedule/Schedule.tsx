import React, { useMemo } from 'react';

import { AppRootProps } from '@grafana/data';
import { getLocationSrv } from '@grafana/runtime';
import {
  Button,
  HorizontalGroup,
  VerticalGroup,
  RadioButtonGroup,
  IconButton,
  ToolbarButton,
  Icon,
  Field,
} from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';
import Draggable from 'react-draggable';

// import Rotations from 'components/Rotations/Rotations';
import PluginLink from 'components/PluginLink/PluginLink';
import ScheduleCounter from 'components/ScheduleCounter/ScheduleCounter';
import ScheduleQuality from 'components/ScheduleQuality/ScheduleQuality';
import Text from 'components/Text/Text';
// import UsersTimezones from 'components/UsersTimezones/UsersTimezones';
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

import { getStartOfWeek, getUTCString } from './Schedule.helpers';

import styles from './Schedule.module.css';

const cx = cn.bind(styles);

interface SchedulePageProps extends AppRootProps, WithStoreProps {}

interface SchedulePageState {
  startMoment: dayjs.Dayjs;
  schedulePeriodType: string;
  renderType: string;
  shiftIdToShowRotationForm?: Shift['id'];
  shiftIdToShowOverridesForm?: Shift['id'];
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
    };
  }

  async componentDidMount() {
    const { store } = this.props;
    const { startMoment } = this.state;

    /*if (!store.hasFeature(AppFeature.WebSchedules)) {
      getLocationSrv().update({ query: { page: 'schedules' } });
    }*/

    store.userStore.updateItems();

    const {
      query: { id },
    } = this.props;

    store.scheduleStore.updateFrequencyOptions();
    store.scheduleStore.updateDaysOptions();
    await store.scheduleStore.updateOncallShifts(id); // TODO we should know shifts to render Rotations

    this.updateEvents();
  }

  componentWillUnmount() {
    const { store } = this.props;

    store.scheduleStore.clearPreview();
  }

  render() {
    const { store } = this.props;
    const { startMoment, schedulePeriodType, renderType, shiftIdToShowRotationForm, shiftIdToShowOverridesForm } =
      this.state;
    const { query } = this.props;
    const { id: scheduleId } = query;

    const users = store.userStore.getSearchResult().results;

    const { scheduleStore, currentTimezone } = store;

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
                {/*<ScheduleCounter
                  type="link"
                  count={5}
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
                  count={2}
                  tooltipTitle="Warnings"
                  tooltipContent="Schedule has unassigned time periods during next 7 days"
                />*/}
              </HorizontalGroup>
              <HorizontalGroup>
                {users && (
                  <HorizontalGroup>
                    <Text type="secondary">Current timezone:</Text>
                    <UserTimezoneSelect value={currentTimezone} users={users} onChange={this.handleTimezoneChange} />
                  </HorizontalGroup>
                )}
                {/*<ScheduleQuality quality={0.89} />*/}
                {/*<ToolbarButton icon="copy" tooltip="Copy" />
                <ToolbarButton icon="brackets-curly" tooltip="Code" />
                <ToolbarButton icon="share-alt" tooltip="Share" />
                <ToolbarButton icon="cog" tooltip="Settings" />*/}
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
              onTzChange={this.handleTimezoneChange}
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
              {/*<HorizontalGroup width="auto">
                <RadioButtonGroup
                  options={[
                    { label: 'Day', value: 'day' },
                    {
                      label: 'Week',
                      value: 'week',
                    },
                    { label: 'Month', value: 'month' },
                    { label: 'Custom', value: 'custom' },
                  ]}
                  value={schedulePeriodType}
                  onChange={this.handleShedulePeriodTypeChange}
                />
                <RadioButtonGroup
                  options={[
                    { label: 'Timeline', value: 'timeline' },
                    {
                      label: 'Grid',
                      value: 'grid',
                    },
                  ]}
                  value={renderType}
                  onChange={this.handleRenderTypeChange}
                />
              </HorizontalGroup>*/}
            </HorizontalGroup>
          </div>
          {/* <div className={'current-time'} />*/}
          <div className={cx('rotations')}>
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
    const {
      store,
      query: { id: scheduleId },
    } = this.props;

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

  handleTodayClick = () => {
    const { store } = this.props;

    this.setState({ startMoment: getStartOfWeek(store.currentTimezone) }, this.updateEvents);
  };

  handleLeftClick = () => {
    const { startMoment } = this.state;

    this.setState({ startMoment: startMoment.add(-7, 'day') }, this.updateEvents);
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

  handleRightClick = () => {
    const { startMoment } = this.state;

    this.setState({ startMoment: startMoment.add(7, 'day') }, this.updateEvents);
  };
}

export default withMobXProviderContext(SchedulePage);
