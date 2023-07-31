import React, { FC, useMemo } from 'react';

import cn from 'classnames/bind';
import dayjs from 'dayjs';

import { Timezone } from 'models/timezone/timezone.types';

import { default_working_hours } from './WorkingHours.config';
import { getNonWorkingMoments, getWorkingMoments } from './WorkingHours.helpers';

import styles from './WorkingHours.module.css';

interface WorkingHoursProps {
  timezone: Timezone;
  workingHours: any;
  startMoment: dayjs.Dayjs;
  duration: number; // in seconds
  className: string;
  light?: boolean;
}

const cx = cn.bind(styles);

const WorkingHours: FC<WorkingHoursProps> = (props) => {
  const { timezone, workingHours = default_working_hours, startMoment, duration, className, light } = props;

  const endMoment = startMoment.add(duration, 'seconds');

  const workingMoments = useMemo(() => {
    return getWorkingMoments(startMoment, endMoment, workingHours, timezone);
  }, [startMoment, endMoment, workingHours, timezone]);

  const nonWorkingMoments = useMemo(() => {
    return getNonWorkingMoments(startMoment, endMoment, workingMoments);
  }, [startMoment, endMoment, workingMoments]);

  return (
    <svg version="1.1" width="100%" height="28px" xmlns="http://www.w3.org/2000/svg" className={className}>
      <defs>
        <pattern id="stripes" patternUnits="userSpaceOnUse" width="10" height="10" patternTransform="rotate(45)">
          <line x1="0" y="0" x2="0" y2="10" stroke="var(--working-hours-shades-color)" strokeWidth="10" />
        </pattern>
        <pattern id="stripes_light" patternUnits="userSpaceOnUse" width="10" height="10" patternTransform="rotate(45)">
          <line x1="0" y="0" x2="0" y2="10" stroke="var(--working-hours-shades-color-light)" strokeWidth="10" />
        </pattern>
      </defs>
      {nonWorkingMoments &&
        nonWorkingMoments.map((moment, index) => {
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
              fill={light ? 'url(#stripes_light)' : 'url(#stripes)'}
            />
          );
        })}
    </svg>
  );
};

export default WorkingHours;
