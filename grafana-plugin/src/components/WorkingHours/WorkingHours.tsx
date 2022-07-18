import React, { FC, useMemo } from 'react';

import cn from 'classnames/bind';
import dayjs from 'dayjs';
import localeData from 'dayjs/plugin/localeData';

import { Timezone } from 'models/timezone/timezone.types';

import { default_working_hours } from './WorkingHours.config';
import { getNonWorkingMoments, getWorkingMoments } from './WorkingHours.helpers';

import styles from './WorkingHours.module.css';

import { start } from 'repl';

interface WorkingHoursProps {
  timezone: Timezone;
  workingHours: any;
  startMoment: dayjs.Dayjs;
  duration: number; // in seconds
  width: number; // in pixels
  className: string;
}

const cx = cn.bind(styles);

const WorkingHours: FC<WorkingHoursProps> = (props) => {
  const {
    timezone,
    workingHours = default_working_hours,
    startMoment = dayjs().utc().startOf('week'),
    duration = 14 * 24 * 60 * 60,
    className,
  } = props;

  const endMoment = startMoment.add(duration, 'seconds');

  const workingMoments = useMemo(
    () => getWorkingMoments(startMoment, endMoment, workingHours, timezone),
    [startMoment, endMoment, workingHours, timezone]
  );

  /*console.log(
    workingMoments.map(({ start, end }) => `${start.diff(startMoment, 'hours')} - ${end.diff(startMoment, 'hours')}`)
  );*/

  const nonWorkingMoments = getNonWorkingMoments(startMoment, endMoment, workingMoments);

  /*console.log(
    workingMoments.map(
      (range) =>
        `${range.start.tz(timezone).format('D MMM ddd HH:ss')} - ${range.end.tz(timezone).format('D MMM ddd HH:ss')}`
    )
  );

  console.log(
    nonWorkingMoments.map(
      (range) =>
        `${range.start.tz(timezone).format('D MMM ddd HH:ss')} - ${range.end.tz(timezone).format('D MMM ddd HH:ss')}`
    )
  );*/

  return (
    <svg version="1.1" width="100%" height="28px" xmlns="http://www.w3.org/2000/svg" className={className}>
      <defs>
        <pattern id="stripes" patternUnits="userSpaceOnUse" width="10" height="10" patternTransform="rotate(45)">
          <line x1="0" y="0" x2="0" y2="10" stroke="rgba(17, 18, 23, 0.15)" strokeWidth="10" />
        </pattern>
      </defs>
      {nonWorkingMoments.map((moment, index) => {
        const start = moment.start.diff(startMoment, 'seconds');
        const diff = moment.end.diff(moment.start, 'seconds');
        return (
          <rect
            className={cx('stripes')}
            key={index}
            x={`${(start * 100) / duration}%`}
            y={0}
            width={`${(diff * 100) / duration}%`}
            height="100%"
            fill="url(#stripes)"
          />
        );
      })}
    </svg>
  );
};

export default WorkingHours;
