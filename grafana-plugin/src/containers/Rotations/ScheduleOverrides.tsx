import React, { Component } from 'react';

import { Button, HorizontalGroup, Tooltip } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';
import { CSSTransition, TransitionGroup } from 'react-transition-group';

import { ScheduleFiltersType } from 'components/ScheduleFilters/ScheduleFilters.types';
import { Text } from 'components/Text/Text';
import { Rotation } from 'containers/Rotation/Rotation';
import { ScheduleOverrideForm } from 'containers/RotationForm/ScheduleOverrideForm';
import { TimelineMarks } from 'containers/TimelineMarks/TimelineMarks';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import {
  getLayersFromStore,
  getOverrideColor,
  getOverridesFromStore,
  getShiftSwapsFromStore,
  SHIFT_SWAP_COLOR,
} from 'models/schedule/schedule.helpers';
import { Schedule, Shift, ShiftEvents, ShiftSwap } from 'models/schedule/schedule.types';
import { getUTCString } from 'pages/schedule/Schedule.helpers';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import { UserActions } from 'utils/authorization/authorization';

import { DEFAULT_TRANSITION_TIMEOUT } from './Rotations.config';
import { findClosestUserEvent, findColor } from './Rotations.helpers';

import styles from './Rotations.module.css';

const cx = cn.bind(styles);

interface ScheduleOverridesProps extends WithStoreProps {
  shiftStartToShowOverrideForm: dayjs.Dayjs;
  shiftEndToShowOverrideForm: dayjs.Dayjs;
  scheduleId: Schedule['id'];
  shiftIdToShowRotationForm?: Shift['id'] | 'new';
  onShowRotationForm: (shiftId: Shift['id'] | 'new') => void;
  onShowShiftSwapForm: (id: ShiftSwap['id'] | 'new', params?: Partial<ShiftSwap>) => void;
  onCreate: () => void;
  onUpdate: () => void;
  onDelete: () => void;
  disabled: boolean;
  disableShiftSwaps: boolean;
  filters: ScheduleFiltersType;
}

interface ScheduleOverridesState {
  shiftStartToShowOverrideForm?: dayjs.Dayjs;
  shiftEndToShowOverrideForm?: dayjs.Dayjs;
}

@observer
class _ScheduleOverrides extends Component<ScheduleOverridesProps, ScheduleOverridesState> {
  state: ScheduleOverridesState = {
    shiftStartToShowOverrideForm: undefined,
    shiftEndToShowOverrideForm: undefined,
  };

  render() {
    const {
      scheduleId,
      onCreate,
      onUpdate,
      onDelete,
      store,
      shiftIdToShowRotationForm,
      disabled,
      disableShiftSwaps,
      shiftStartToShowOverrideForm: propsShiftStartToShowOverrideForm,
      shiftEndToShowOverrideForm: propsShiftEndToShowOverrideForm,
      onShowShiftSwapForm,
      filters,
      store: {
        userStore: { currentUserPk },
      },
    } = this.props;
    const { shiftStartToShowOverrideForm, shiftEndToShowOverrideForm } = this.state;

    const shifts = getOverridesFromStore(store, scheduleId, store.timezoneStore.calendarStartDate) as ShiftEvents[];

    const layers = getLayersFromStore(store, scheduleId, store.timezoneStore.calendarStartDate);

    const shiftSwaps = getShiftSwapsFromStore(store, scheduleId, store.timezoneStore.calendarStartDate);

    const base = 7 * 24 * 60; // in minutes
    const diff = store.timezoneStore.currentDateInSelectedTimezone.diff(
      store.timezoneStore.calendarStartDate,
      'minutes'
    );

    const currentTimeX = diff / base;

    const currentTimeHidden = currentTimeX < 0 || currentTimeX > 1;

    const schedule = store.scheduleStore.items[scheduleId];

    const isTypeReadOnly = !schedule?.enable_web_overrides;

    return (
      <>
        <div id="overrides-list" className={cx('root')}>
          <div className={cx('header')}>
            <HorizontalGroup justify="space-between">
              <div className={cx('title')}>
                <Text.Title level={4} type="primary">
                  Overrides and swaps
                </Text.Title>
              </div>
              <HorizontalGroup>
                <Button
                  variant="secondary"
                  disabled={disableShiftSwaps}
                  onClick={() => {
                    const closestEvent = findClosestUserEvent(dayjs(), currentUserPk, layers);
                    const swapStart = closestEvent
                      ? dayjs(closestEvent.start)
                      : store.timezoneStore.currentDateInSelectedTimezone.startOf('day').add(1, 'day');

                    const swapEnd = closestEvent ? dayjs(closestEvent.end) : swapStart.add(1, 'day');

                    onShowShiftSwapForm('new', {
                      swap_start: getUTCString(swapStart),
                      swap_end: getUTCString(swapEnd),
                    });
                  }}
                >
                  Request shift swap
                </Button>
                {isTypeReadOnly ? (
                  <Tooltip content="You can set an override using the override calendar" placement="top">
                    <div>
                      <Button variant="primary" icon="plus" disabled>
                        Add override
                      </Button>
                    </div>
                  </Tooltip>
                ) : (
                  <WithPermissionControlTooltip userAction={UserActions.SchedulesWrite}>
                    <Button disabled={disabled} icon="plus" onClick={this.handleAddOverride} variant="secondary">
                      Add override
                    </Button>
                  </WithPermissionControlTooltip>
                )}
              </HorizontalGroup>
            </HorizontalGroup>
          </div>
          <div className={cx('header-plus-content')}>
            {!currentTimeHidden && <div className={cx('current-time')} style={{ left: `${currentTimeX * 100}%` }} />}
            <TimelineMarks />
            <TransitionGroup className={cx('rotations')}>
              {shiftSwaps && shiftSwaps.length
                ? shiftSwaps.map(({ isPreview, events }, index) => (
                    <CSSTransition key={index} timeout={DEFAULT_TRANSITION_TIMEOUT} classNames={{ ...styles }}>
                      <Rotation
                        events={events}
                        color={SHIFT_SWAP_COLOR}
                        onSlotClick={(event) => {
                          if (event.is_gap) {
                            return;
                          }
                          onShowShiftSwapForm(event.shiftSwapId);
                        }}
                        transparent={isPreview}
                        filters={filters}
                      />
                    </CSSTransition>
                  ))
                : null}
            </TransitionGroup>
            <TransitionGroup className={cx('rotations')}>
              {shifts && shifts.length ? (
                shifts.map(({ shiftId, isPreview, events }, index) => (
                  <CSSTransition key={index} timeout={DEFAULT_TRANSITION_TIMEOUT} classNames={{ ...styles }}>
                    <Rotation
                      events={events}
                      color={getOverrideColor(index)}
                      onClick={(shiftStart, shiftEnd) => {
                        this.onRotationClick(shiftId, shiftStart, shiftEnd);
                      }}
                      transparent={isPreview}
                      filters={filters}
                    />
                  </CSSTransition>
                ))
              ) : (
                <CSSTransition key={0} timeout={DEFAULT_TRANSITION_TIMEOUT} classNames={{ ...styles }}>
                  <Rotation
                    key={0}
                    events={[]}
                    onClick={(shiftStart, shiftEnd) => {
                      this.onRotationClick('new', shiftStart, shiftEnd);
                    }}
                  />
                </CSSTransition>
              )}
            </TransitionGroup>
          </div>
        </div>
        {shiftIdToShowRotationForm && (
          <ScheduleOverrideForm
            shiftId={shiftIdToShowRotationForm}
            shiftColor={findColor(shiftIdToShowRotationForm, undefined, shifts)}
            scheduleId={scheduleId}
            shiftStart={propsShiftStartToShowOverrideForm || shiftStartToShowOverrideForm}
            shiftEnd={propsShiftEndToShowOverrideForm || shiftEndToShowOverrideForm}
            onHide={() => {
              this.handleHide();

              store.scheduleStore.clearPreview();
            }}
            onUpdate={() => {
              this.handleHide();

              onUpdate();
            }}
            onCreate={() => {
              this.handleHide();

              onCreate();
            }}
            onDelete={() => {
              this.handleHide();

              onDelete();
            }}
          />
        )}
      </>
    );
  }

  onRotationClick = (shiftId: Shift['id'], shiftStart: dayjs.Dayjs, shiftEnd: dayjs.Dayjs) => {
    const { disabled } = this.props;

    if (disabled) {
      return;
    }

    this.setState({ shiftStartToShowOverrideForm: shiftStart, shiftEndToShowOverrideForm: shiftEnd }, () => {
      this.onShowRotationForm(shiftId);
    });
  };

  handleAddOverride = () => {
    const { store, disabled } = this.props;

    if (disabled) {
      return;
    }

    // use start of current day as default start time for override
    this.setState(
      { shiftStartToShowOverrideForm: store.timezoneStore.currentDateInSelectedTimezone.startOf('day') },
      () => {
        this.onShowRotationForm('new');
      }
    );
  };

  handleHide = () => {
    this.setState({ shiftStartToShowOverrideForm: undefined, shiftEndToShowOverrideForm: undefined }, () => {
      this.onShowRotationForm(undefined);
    });
  };

  onShowRotationForm = (shiftId: Shift['id']) => {
    const { onShowRotationForm } = this.props;

    onShowRotationForm(shiftId);
  };
}

export const ScheduleOverrides = withMobXProviderContext(_ScheduleOverrides);
