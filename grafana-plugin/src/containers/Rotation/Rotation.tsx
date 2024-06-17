import React, { FC, useMemo } from 'react';

import { HorizontalGroup, LoadingPlaceholder } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';
import hash from 'object-hash';

import { ScheduleFiltersType } from 'components/ScheduleFilters/ScheduleFilters.types';
import { Text } from 'components/Text/Text';
import { ScheduleSlot } from 'containers/ScheduleSlot/ScheduleSlot';
import { scheduleViewToDaysInOneRow } from 'models/schedule/schedule.helpers';
import { Event, ScheduleView, ShiftSwap } from 'models/schedule/schedule.types';
import { useStore } from 'state/useStore';

import styles from './Rotation.module.css';

const cx = cn.bind(styles);

interface RotationProps {
  layerIndex?: number;
  rotationIndex?: number;
  color?: string;
  events: Event[];
  onClick?: (start: dayjs.Dayjs, end: dayjs.Dayjs) => void;
  handleAddOverride?: (start: dayjs.Dayjs, end: dayjs.Dayjs) => void;
  handleAddShiftSwap?: (id: 'new', params: Partial<ShiftSwap>) => void;
  handleOpenSchedule?: (event: Event) => void;
  onShiftSwapClick?: (swapId: ShiftSwap['id']) => void;
  transparent?: boolean;
  simplified?: boolean;
  filters?: ScheduleFiltersType;
  getColor?: (event: Event) => string;
  onSlotClick?: (event: Event) => void;
  emptyText?: string;
  showScheduleNameAsSlotTitle?: boolean;
  startDate?: dayjs.Dayjs;
  scheduleView?: ScheduleView;
}

export const Rotation: FC<RotationProps> = observer((props) => {
  const {
    timezoneStore: { calendarStartDate, getDateInSelectedTimezone, selectedTimezoneOffset },
    scheduleStore: { scheduleView: storeScheduleView },
  } = useStore();
  const {
    events,
    color: propsColor,
    transparent = false,
    onClick,
    handleAddOverride,
    handleAddShiftSwap,
    handleOpenSchedule,
    onShiftSwapClick,
    simplified,
    filters,
    getColor,
    onSlotClick,
    emptyText,
    showScheduleNameAsSlotTitle,
    startDate: propsStartDate,
    scheduleView: propsScheduleView,
  } = props;

  const scheduleView = propsScheduleView || storeScheduleView;

  const startDate = propsStartDate || calendarStartDate;

  const days = scheduleViewToDaysInOneRow[scheduleView];

  const handleRotationClick = (event: React.MouseEvent<HTMLDivElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = event.clientX - rect.left; //x position within the element.
    const width = event.currentTarget.offsetWidth;

    const dayOffset = Math.floor((x / width) * scheduleViewToDaysInOneRow[scheduleView]);

    const shiftStart = startDate.add(dayOffset, 'day');
    const shiftEnd = shiftStart.add(1, 'day');

    onClick(shiftStart, shiftEnd);
  };

  const getAddOverrideClickHandler = (scheduleEvent: Event) => {
    if (simplified) {
      return undefined;
    }

    return (event: React.MouseEvent<HTMLDivElement>) => {
      event.stopPropagation();

      handleAddOverride(dayjs(scheduleEvent.start), dayjs(scheduleEvent.end));
    };
  };

  const getAddShiftSwapClickHandler = (scheduleEvent: Event) => {
    if (simplified) {
      return undefined;
    }

    return (event: React.MouseEvent<HTMLDivElement>) => {
      event.stopPropagation();

      handleAddShiftSwap('new', {
        swap_start: scheduleEvent.start,
        swap_end: scheduleEvent.end,
      });
    };
  };

  const getOpenScheduleClickHandler = (scheduleEvent: Event) => {
    if (!handleOpenSchedule) {
      return undefined;
    }

    return (event: React.MouseEvent<HTMLDivElement>) => {
      event.stopPropagation();

      handleOpenSchedule(scheduleEvent);
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
    const firstShiftOffset = getDateInSelectedTimezone(firstShift.start).diff(
      getDateInSelectedTimezone(startDate),
      'seconds'
    );
    const base = 60 * 60 * 24 * days;

    return firstShiftOffset / base;
  }, [events, startDate, selectedTimezoneOffset]);

  return (
    <div className={cx('root')} onClick={onClick && handleRotationClick}>
      <div className={cx('timeline')}>
        {events ? (
          events.length ? (
            <div
              className={cx('slots', { slots__transparent: transparent })}
              style={{ transform: `translate(${x * 100}%, 0)` }}
            >
              {events.map((event) => {
                return (
                  <ScheduleSlot
                    scheduleView={scheduleView}
                    key={hash(event)}
                    event={event}
                    color={propsColor || getColor(event)}
                    handleAddOverride={getAddOverrideClickHandler(event)}
                    handleAddShiftSwap={getAddShiftSwapClickHandler(event)}
                    handleOpenSchedule={getOpenScheduleClickHandler(event)}
                    onShiftSwapClick={onShiftSwapClick}
                    filters={filters}
                    onClick={getSlotClickHandler(event)}
                    showScheduleNameAsSlotTitle={showScheduleNameAsSlotTitle}
                  />
                );
              })}
            </div>
          ) : (
            <Empty text={emptyText} />
          )
        ) : (
          <HorizontalGroup align="center" justify="center">
            <LoadingPlaceholder text="Loading shifts..." />
          </HorizontalGroup>
        )}
      </div>
    </div>
  );
});

const Empty = ({ text }: { text: string }) => {
  return (
    <div className={cx('empty')}>
      <Text type="secondary">{text}</Text>
    </div>
  );
};
