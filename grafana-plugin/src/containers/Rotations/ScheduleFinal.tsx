import React, { FC, useMemo } from 'react';

import { HorizontalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';
import { CSSTransition, TransitionGroup } from 'react-transition-group';

import { ScheduleFiltersType } from 'components/ScheduleFilters/ScheduleFilters.types';
import { Text } from 'components/Text/Text';
import { Rotation } from 'containers/Rotation/Rotation';
import { TimelineMarks } from 'containers/TimelineMarks/TimelineMarks';
import {
  flattenShiftEvents,
  getLayersFromStore,
  getOverridesFromStore,
  getShiftsFromStore,
  getTotalDaysToDisplay,
  scheduleViewToDaysInOneRow,
} from 'models/schedule/schedule.helpers';
import { Event, Schedule, ScheduleView, ShiftSwap } from 'models/schedule/schedule.types';
import { getCurrentTimeX } from 'pages/schedule/Schedule.helpers';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';

import { DEFAULT_TRANSITION_TIMEOUT } from './Rotations.config';
import { findColor } from './Rotations.helpers';

import styles from './Rotations.module.css';

const cx = cn.bind(styles);

interface ScheduleFinalProps extends WithStoreProps {
  scheduleId: Schedule['id'];
  simplified?: boolean;
  onShowOverrideForm: (shiftId: 'new', shiftStart: dayjs.Dayjs, shiftEnd: dayjs.Dayjs) => void;
  onShowShiftSwapForm: (id: ShiftSwap['id'] | 'new', params?: Partial<ShiftSwap>) => void;
  disabled?: boolean;
  filters: ScheduleFiltersType;
  onSlotClick?: (event: Event) => void;
  scheduleView?: ScheduleView;
}

const _ScheduleFinal: FC<ScheduleFinalProps> = observer(
  ({
    store,
    simplified,
    scheduleId,
    filters,
    onShowShiftSwapForm,
    onShowOverrideForm,
    onSlotClick,
    scheduleView: propsScheduleView,
  }) => {
    const {
      timezoneStore: { currentDateInSelectedTimezone, calendarStartDate },
      scheduleStore: { scheduleView: storeScheduleView },
    } = store;

    const scheduleView = propsScheduleView || storeScheduleView;

    const shifts = flattenShiftEvents(getShiftsFromStore(store, scheduleId, calendarStartDate));

    const layers = getLayersFromStore(store, scheduleId, calendarStartDate);

    const overrides = getOverridesFromStore(store, scheduleId, calendarStartDate);

    const getColor = (event: Event) => findColor(event.shift?.pk, layers, overrides);

    const handleShowOverrideForm = (shiftStart: dayjs.Dayjs, shiftEnd: dayjs.Dayjs) => {
      onShowOverrideForm('new', shiftStart, shiftEnd);
    };

    const rows = useMemo(() => {
      const totalDays = getTotalDaysToDisplay(scheduleView, calendarStartDate);
      const rows = [];
      for (let i = 0; i < totalDays / scheduleViewToDaysInOneRow[scheduleView]; i++) {
        rows.push({
          startDate: calendarStartDate.add(scheduleViewToDaysInOneRow[scheduleView] * i, 'days'),
        });
      }
      return rows;
    }, [calendarStartDate, scheduleView]);

    return (
      <div className={cx('root')}>
        {!simplified && (
          <div className={cx('header')}>
            <HorizontalGroup justify="space-between">
              <Text.Title level={5} type="primary">
                Final schedule
              </Text.Title>
            </HorizontalGroup>
          </div>
        )}
        <div className={cx('header-plus-content')}>
          {rows.map(({ startDate }, index) => (
            <TransitionGroup key={index} className={cx('u-position-relative', 'layer', 'layer-first')}>
              <TimelineMarks
                scheduleView={scheduleView}
                startDate={startDate}
                withBorderBottom={index !== rows.length - 1}
              />
              <div
                className={cx('current-time')}
                style={{
                  left: `${
                    getCurrentTimeX(
                      currentDateInSelectedTimezone,
                      startDate,
                      scheduleViewToDaysInOneRow[scheduleView] * 24 * 60
                    ) * 100
                  }%`,
                }}
              />
              {shifts?.length ? (
                shifts.map(({ events }, index) => {
                  return (
                    <CSSTransition key={index} timeout={DEFAULT_TRANSITION_TIMEOUT} classNames={{ ...styles }}>
                      <Rotation
                        scheduleView={scheduleView}
                        startDate={startDate}
                        key={index}
                        events={events}
                        handleAddOverride={handleShowOverrideForm}
                        handleAddShiftSwap={onShowShiftSwapForm}
                        onShiftSwapClick={onShowShiftSwapForm}
                        simplified={simplified}
                        filters={filters}
                        getColor={getColor}
                        onSlotClick={onSlotClick}
                      />
                    </CSSTransition>
                  );
                })
              ) : (
                <CSSTransition key={0} timeout={DEFAULT_TRANSITION_TIMEOUT} classNames={{ ...styles }}>
                  <Rotation scheduleView={scheduleView} startDate={calendarStartDate} events={[]} />
                </CSSTransition>
              )}
            </TransitionGroup>
          ))}
        </div>
      </div>
    );
  }
);

export const ScheduleFinal = withMobXProviderContext(_ScheduleFinal);
