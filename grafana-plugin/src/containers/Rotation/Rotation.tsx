import React, { FC, useMemo, useState } from 'react';

import { HorizontalGroup, LoadingPlaceholder } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';
import hash from 'object-hash';

import { ScheduleFiltersType } from 'components/ScheduleFilters/ScheduleFilters.types';
import { Text } from 'components/Text/Text';
import { ScheduleSlot } from 'containers/ScheduleSlot/ScheduleSlot';
import { Event, RotationFormLiveParams, ShiftSwap } from 'models/schedule/schedule.types';
import { useStore } from 'state/useStore';

import { RotationTutorial } from './RotationTutorial';

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
  days?: number;
  transparent?: boolean;
  tutorialParams?: RotationFormLiveParams;
  simplified?: boolean;
  filters?: ScheduleFiltersType;
  getColor?: (event: Event) => string;
  onSlotClick?: (event: Event) => void;
  emptyText?: string;
  showScheduleNameAsSlotTitle?: boolean;
}

export const Rotation: FC<RotationProps> = observer((props) => {
  const {
    timezoneStore: { calendarStartDate },
  } = useStore();
  const {
    events,
    color: propsColor,
    days = 7,
    transparent = false,
    tutorialParams,
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
  } = props;

  const [animate, _setAnimate] = useState<boolean>(true);

  const handleRotationClick = (event: React.MouseEvent<HTMLDivElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = event.clientX - rect.left; //x position within the element.
    const width = event.currentTarget.offsetWidth;

    const dayOffset = Math.floor((x / width) * 7);

    const shiftStart = calendarStartDate.add(dayOffset, 'day');
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
    const firstShiftOffset = dayjs(firstShift.start).diff(calendarStartDate, 'seconds');
    const base = 60 * 60 * 24 * days;

    return firstShiftOffset / base;
  }, [events]);

  return (
    <div className={cx('root')} onClick={onClick && handleRotationClick}>
      <div className={cx('timeline')}>
        {tutorialParams && <RotationTutorial {...tutorialParams} />}
        {events ? (
          events.length ? (
            <div
              className={cx('slots', { slots__animate: animate, slots__transparent: transparent })}
              style={{ transform: `translate(${x * 100}%, 0)` }}
            >
              {events.map((event) => {
                return (
                  <ScheduleSlot
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
