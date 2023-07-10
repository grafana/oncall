import React, { Component } from 'react';

import { HorizontalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';
import { CSSTransition, TransitionGroup } from 'react-transition-group';

import { ScheduleFiltersType } from 'components/ScheduleFilters/ScheduleFilters.types';
import Text from 'components/Text/Text';
import TimelineMarks from 'components/TimelineMarks/TimelineMarks';
import Rotation from 'containers/Rotation/Rotation';
import { getLayersFromStore, getOverridesFromStore, getShiftsFromStore } from 'models/schedule/schedule.helpers';
import { Schedule, Shift } from 'models/schedule/schedule.types';
import { Timezone } from 'models/timezone';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';

import { DEFAULT_TRANSITION_TIMEOUT } from './Rotations.config';
import { findColor } from './Rotations.helpers';

import styles from './Rotations.module.css';

const cx = cn.bind(styles);

interface ScheduleFinalProps extends WithStoreProps {
  startMoment: dayjs.Dayjs;
  currentTimezone: Timezone;
  scheduleId: Schedule['id'];
  simplified?: boolean;
  onClick: (shiftId: Shift['id']) => void;
  onShowOverrideForm: (shiftId: 'new', shiftStart: dayjs.Dayjs, shiftEnd: dayjs.Dayjs) => void;
  disabled?: boolean;
  filters: ScheduleFiltersType;
}

interface ScheduleOverridesState {
  searchTerm: string;
}

@observer
class ScheduleFinal extends Component<ScheduleFinalProps, ScheduleOverridesState> {
  state: ScheduleOverridesState = {
    searchTerm: '',
  };

  render() {
    const { startMoment, currentTimezone, store, simplified, scheduleId, filters } = this.props;

    const base = 7 * 24 * 60; // in minutes
    const diff = dayjs().tz(currentTimezone).diff(startMoment, 'minutes');

    const currentTimeX = diff / base;

    const shifts = getShiftsFromStore(store, scheduleId, startMoment);

    const layers = getLayersFromStore(store, scheduleId, startMoment);

    const overrides = getOverridesFromStore(store, scheduleId, startMoment);

    const currentTimeHidden = currentTimeX < 0 || currentTimeX > 1;

    return (
      <>
        <div className={cx('root')}>
          {!simplified && (
            <div className={cx('header')}>
              <HorizontalGroup justify="space-between">
                <div className={cx('title')}>
                  <Text.Title level={4} type="primary">
                    Final schedule
                  </Text.Title>
                </div>
              </HorizontalGroup>
            </div>
          )}
          <div className={cx('header-plus-content')}>
            {!currentTimeHidden && <div className={cx('current-time')} style={{ left: `${currentTimeX * 100}%` }} />}
            <TimelineMarks startMoment={startMoment} timezone={currentTimezone} />
            <TransitionGroup className={cx('rotations')}>
              {shifts && shifts.length ? (
                shifts.map(({ shiftId, events }, index) => {
                  return (
                    <CSSTransition key={index} timeout={DEFAULT_TRANSITION_TIMEOUT} classNames={{ ...styles }}>
                      <Rotation
                        key={index}
                        scheduleId={scheduleId}
                        events={events}
                        startMoment={startMoment}
                        currentTimezone={currentTimezone}
                        color={findColor(shiftId, layers, overrides)}
                        onClick={this.getRotationClickHandler(shiftId)}
                        handleAddOverride={this.handleShowOverrideForm}
                        simplified={simplified}
                        filters={filters}
                      />
                    </CSSTransition>
                  );
                })
              ) : (
                <CSSTransition key={0} timeout={DEFAULT_TRANSITION_TIMEOUT} classNames={{ ...styles }}>
                  <Rotation
                    scheduleId={scheduleId}
                    events={[]}
                    startMoment={startMoment}
                    currentTimezone={currentTimezone}
                  />
                </CSSTransition>
              )}
            </TransitionGroup>
          </div>
        </div>
      </>
    );
  }

  getRotationClickHandler = (shiftId: Shift['id']) => {
    const { onClick, disabled } = this.props;

    return () => {
      if (disabled) {
        return;
      }

      onClick(shiftId);
    };
  };

  onSearchTermChangeCallback = () => {};

  handleShowOverrideForm = (shiftStart: dayjs.Dayjs, shiftEnd: dayjs.Dayjs) => {
    const { onShowOverrideForm } = this.props;

    onShowOverrideForm('new', shiftStart, shiftEnd);
  };
}

export default withMobXProviderContext(ScheduleFinal);
