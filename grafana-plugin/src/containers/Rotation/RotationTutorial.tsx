import React, { FC, useMemo } from 'react';

import cn from 'classnames/bind';
import dayjs from 'dayjs';

import { RotationFormLiveParams } from 'models/schedule/schedule.types';

import styles from './Rotation.module.css';

const cx = cn.bind(styles);

interface RotationProps extends RotationFormLiveParams {
  startMoment: dayjs.Dayjs;
  days?: number;
}

const RotationTutorial: FC<RotationProps> = (props) => {
  const { startMoment, days = 7, shiftStart, shiftEnd, rotationStart, focusElementName } = props;

  const duration = shiftEnd.diff(shiftStart, 'seconds');

  const events = useMemo(() => {
    return [
      {
        start: dayjs(shiftStart),
        end: dayjs(shiftStart).add(duration, 'seconds'),
      },
    ];
  }, [shiftStart, duration]);

  const base = 60 * 60 * 24 * days;

  const pointerX = useMemo(() => {
    if (focusElementName === undefined) {
      return undefined;
    }

    const moment = props[focusElementName];
    const firstEvent = events[0];
    const diff = dayjs(moment).diff(firstEvent.start, 'seconds');

    return diff / base;
  }, [focusElementName, events, rotationStart]);

  const x = useMemo(() => {
    if (!events || !events.length) {
      return 0;
    }

    const firstEvent = events[0];
    const firstShiftOffset = dayjs(firstEvent.start).diff(startMoment, 'seconds');
    const base = 60 * 60 * 24 * days;

    return firstShiftOffset / base;
  }, [events, startMoment]);

  return (
    <div className={cx('slots', 'slots--tutorial')} style={{ transform: `translate(${x * 100}%, 0)` }}>
      <Pointer
        className={cx('pointer', { 'pointer--active': pointerX !== undefined })}
        style={{ left: `calc(${pointerX * 100}% - 5px)` }}
      />
      {events.map((event, index) => {
        const duration = event.end.diff(event.start, 'seconds');
        const width = duration / base;
        return (
          <TutorialSlot
            active={focusElementName === 'shiftStart' || focusElementName === 'shiftEnd'}
            style={{ width: `${width * 100}%` }}
            key={index}
          />
        );
      })}
    </div>
  );
};

const TutorialSlot = (props: { style: React.CSSProperties; active: boolean }) => {
  const { style, active } = props;

  return <div className={cx('tutorial-slot', { 'tutorial-slot--active': active })} style={style} />;
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
