import React, { FC, useMemo, useState } from 'react';

import { HorizontalGroup, LoadingPlaceholder } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';

import ScheduleSlot from 'containers/ScheduleSlot/ScheduleSlot';
import { Schedule, Event, RotationFormLiveParams } from 'models/schedule/schedule.types';
import { Timezone } from 'models/timezone/timezone.types';

import { getLabel } from './Rotation.helpers';
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
  days?: number;
  transparent?: boolean;
  tutorialParams?: RotationFormLiveParams;
  simplified?: boolean;
}

const Rotation: FC<RotationProps> = (props) => {
  const {
    events,
    scheduleId,
    layerIndex,
    rotationIndex,
    startMoment,
    currentTimezone,
    color,
    days = 7,
    transparent = false,
    tutorialParams,
    onClick,
    handleAddOverride,
    simplified,
  } = props;

  const [animate, _setAnimate] = useState<boolean>(true);

  const handleRotationClick = (event) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = event.clientX - rect.left; //x position within the element.
    const width = event.currentTarget.offsetWidth;

    const dayOffset = Math.floor((x / width) * 7);

    const shiftStart = startMoment.add(dayOffset, 'day');
    const shiftEnd = shiftStart.add(1, 'day');

    onClick(shiftStart, shiftEnd);
  };

  const getAddOverrideClickHandler = (scheduleEvent) => {
    return (event) => {
      event.stopPropagation();

      handleAddOverride(dayjs(scheduleEvent.start), dayjs(scheduleEvent.end));
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

  let eventIndexToShowLabel = -1;
  if (!isNaN(layerIndex) && !isNaN(rotationIndex)) {
    eventIndexToShowLabel = events.findIndex((event) => dayjs(event.start).isSameOrAfter(startMoment));
  }

  return (
    <div className={cx('root')} onClick={handleRotationClick}>
      <div className={cx('timeline')}>
        {tutorialParams && <RotationTutorial startMoment={startMoment} {...tutorialParams} />}
        {events ? (
          events.length ? (
            <div
              className={cx('slots', { slots__animate: animate, slots__transparent: transparent })}
              style={{ transform: `translate(${x * 100}%, 0)` }}
            >
              {events.map((event, index) => {
                return (
                  <ScheduleSlot
                    scheduleId={scheduleId}
                    key={event.start}
                    event={event}
                    startMoment={startMoment}
                    currentTimezone={currentTimezone}
                    color={color}
                    label={index === eventIndexToShowLabel && getLabel(layerIndex, rotationIndex)}
                    handleAddOverride={getAddOverrideClickHandler(event)}
                    simplified={simplified}
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
