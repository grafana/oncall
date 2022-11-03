import React, { FC, useMemo, useState } from 'react';

import cn from 'classnames/bind';
import dayjs from 'dayjs';

import { Schedule, Event, ScheduleType } from 'models/schedule/schedule.types';
import { Timezone } from 'models/timezone/timezone.types';

import styles from './Rotation.module.css';

const cx = cn.bind(styles);

interface RotationProps {
  scheduleId: Schedule['id'];
  startMoment: dayjs.Dayjs;
  currentTimezone: Timezone;
  days?: number;
}

const RotationTutorial: FC<RotationProps> = (props) => {
  const { startMoment, days = 7 /* shiftStart, shiftEnd, rotationStart*/ } = props;

  const shiftStart = dayjs(startMoment);
  const shiftEnd = dayjs(startMoment).add(1, 'days');
  const rotationStart = dayjs(startMoment).add(1, 'days');

  const duration = shiftEnd.diff(shiftStart, 'seconds');

  const events = useMemo(() => {
    const events = [];
    for (let i = 0; i < days; i++) {
      events.push({
        start: dayjs(shiftStart).add(i, 'days'),
        end: dayjs(shiftStart).add(duration, 'seconds').add(i, 'days'),
      });
    }
    return events;
  }, []);

  const base = 60 * 60 * 24 * 7;

  const diff = dayjs(rotationStart).diff(startMoment, 'seconds');

  const currentTimeX = diff / base;

  const x = useMemo(() => {
    if (!events || !events.length) {
      return 0;
    }

    const firstEvent = events[0];
    const firstShiftOffset = dayjs(firstEvent.start).diff(startMoment, 'seconds');
    const base = 60 * 60 * 24 * days;

    return firstShiftOffset / base;
  }, [events]);

  return (
    <div className={cx('slots', 'slots--tutorial')} style={{ transform: `translate(${x * 100}%, 0)` }}>
      <Pointer className={cx('pointer')} style={{ left: `calc(${currentTimeX * 100}% - 5px)` }} />
      {events.map((event, index) => {
        const duration = event.end.diff(event.start, 'seconds');
        const width = duration / base;
        return <TutorialSlot style={{ width: `${width * 100}%` }} key={index} />;
      })}
    </div>
  );
};

const TutorialSlot = (props: { style: React.CSSProperties }) => {
  const { style } = props;

  return <div className={cx('tutorial-slot')} style={style} />;
};

const Pointer = (props: { className: string; style: React.CSSProperties }) => {
  const { className, style } = props;

  return (
    <svg
      className={className}
      style={style}
      width="9"
      height="9"
      viewBox="0 0 9 9"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path d="M4.5 9L0.602887 2.25L8.39711 2.25L4.5 9Z" fill="url(#paint0_linear_2230_44915)" />
      <defs>
        <linearGradient
          id="paint0_linear_2230_44915"
          x1="4.5"
          y1="6.65625"
          x2="4.5"
          y2="-2.33215e-07"
          gradientUnits="userSpaceOnUse"
        >
          <stop stopColor="#F55F3E" />
          <stop offset="1" stopColor="#FF8833" />
        </linearGradient>
      </defs>
    </svg>
  );
};

export default RotationTutorial;
