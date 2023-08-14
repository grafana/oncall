import React, { FC, useMemo, useState } from 'react';

import { HorizontalGroup, LoadingPlaceholder } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import hash from 'object-hash';

import { ScheduleFiltersType } from 'components/ScheduleFilters/ScheduleFilters.types';
import ScheduleSlot from 'containers/ScheduleSlot/ScheduleSlot';
import { Schedule, Event, RotationFormLiveParams, Shift, ShiftSwap } from 'models/schedule/schedule.types';
import { Timezone } from 'models/timezone/timezone.types';

import RotationTutorial from './RotationTutorial';

import styles from './Rotation.module.css';

const cx = cn.bind(styles);

interface RotationProps {
  scheduleId: Schedule['id'];
  startMoment: dayjs.Dayjs;
  currentTimezone: Timezone;
  layerIndex?: number;
  rotationIndex?: number;
  color?: string;
  events: Event[];
  onClick?: (start: dayjs.Dayjs, end: dayjs.Dayjs) => void;
  handleAddOverride?: (start: dayjs.Dayjs, end: dayjs.Dayjs) => void;
  handleAddShiftSwap?: (id: 'new', params: Partial<ShiftSwap>) => void;
  onShiftSwapClick?: (swapId: ShiftSwap['id']) => void;
  days?: number;
  transparent?: boolean;
  tutorialParams?: RotationFormLiveParams;
  simplified?: boolean;
  filters?: ScheduleFiltersType;
  getColor?: (shiftId: Shift['id']) => string;
  onSlotClick?: (event: Event) => void;
}

const Rotation: FC<RotationProps> = (props) => {
  const {
    events,
    scheduleId,
    startMoment,
    currentTimezone,
    color: propsColor,
    days = 7,
    transparent = false,
    tutorialParams,
    onClick,
    handleAddOverride,
    handleAddShiftSwap,
    onShiftSwapClick,
    simplified,
    filters,
    getColor,
    onSlotClick,
  } = props;

  const [animate, _setAnimate] = useState<boolean>(true);

  const handleRotationClick = (event: React.MouseEvent<HTMLDivElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = event.clientX - rect.left; //x position within the element.
    const width = event.currentTarget.offsetWidth;

    const dayOffset = Math.floor((x / width) * 7);

    const shiftStart = startMoment.add(dayOffset, 'day');
    const shiftEnd = shiftStart.add(1, 'day');

    onClick(shiftStart, shiftEnd);
  };

  const getAddOverrideClickHandler = (scheduleEvent: Event) => {
    return (event: React.MouseEvent<HTMLDivElement>) => {
      event.stopPropagation();

      handleAddOverride(dayjs(scheduleEvent.start), dayjs(scheduleEvent.end));
    };
  };

  const getAddShiftSwapClickHandler = (scheduleEvent: Event) => {
    return (event: React.MouseEvent<HTMLDivElement>) => {
      event.stopPropagation();

      handleAddShiftSwap('new', {
        swap_start: scheduleEvent.start,
        swap_end: scheduleEvent.end,
      });
    };
  };

  const getSlotClickHandler = (event: Event) => {
    if (!onSlotClick) {
      return undefined;
    }
    return (e) => {
      e.stopPropagation();

      onSlotClick(event);
    };
  };

  const x = useMemo(() => {
    if (!events || !events.length) {
      return 0;
    }

    const firstShift = events[0];
    const firstShiftOffset = dayjs(firstShift.start).diff(startMoment, 'seconds');
    const base = 60 * 60 * 24 * days;

    return firstShiftOffset / base;
  }, [events]);

  return (
    <div className={cx('root')} onClick={onClick && handleRotationClick}>
      <div className={cx('timeline')}>
        {tutorialParams && <RotationTutorial startMoment={startMoment} {...tutorialParams} />}
        {events ? (
          events.length ? (
            <div
              className={cx('slots', { slots__animate: animate, slots__transparent: transparent })}
              style={{ transform: `translate(${x * 100}%, 0)` }}
            >
              {events.map((event) => {
                return (
                  <ScheduleSlot
                    scheduleId={scheduleId}
                    key={hash(event)}
                    event={event}
                    startMoment={startMoment}
                    currentTimezone={currentTimezone}
                    color={propsColor || getColor(event.shift?.pk)}
                    handleAddOverride={getAddOverrideClickHandler(event)}
                    handleAddShiftSwap={getAddShiftSwapClickHandler(event)}
                    onShiftSwapClick={onShiftSwapClick}
                    simplified={simplified}
                    filters={filters}
                    onClick={getSlotClickHandler(event)}
                  />
                );
              })}
            </div>
          ) : (
            <Empty />
          )
        ) : (
          <HorizontalGroup align="center" justify="center">
            <LoadingPlaceholder text="Loading shifts..." />
          </HorizontalGroup>
        )}
      </div>
    </div>
  );
};

const Empty = () => {
  return <div className={cx('empty')} />;
};

export default Rotation;
