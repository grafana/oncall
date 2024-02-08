import React, { FC, useMemo } from 'react';

import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';

import { Text } from 'components/Text/Text';
import { useStore } from 'state/useStore';

import styles from './TimelineMarks.module.scss';

interface TimelineMarksProps {
  debug?: boolean;
}

const cx = cn.bind(styles);

export const TimelineMarks: FC<TimelineMarksProps> = observer((props) => {
  const {
    timezoneStore: { currentDateInSelectedTimezone, calendarStartDate },
  } = useStore();
  const { debug } = props;

  const momentsToRender = useMemo(() => {
    const hoursToSplit = 12;

    const momentsToRender = [];
    const jLimit = 24 / hoursToSplit;

    for (let i = 0; i < 7; i++) {
      const d = dayjs(calendarStartDate).add(i, 'days');
      const obj = { moment: d, moments: [] };
      for (let j = 0; j < jLimit; j++) {
        const m = dayjs(d).add(j * hoursToSplit, 'hour');
        obj.moments.push(m);
      }
      momentsToRender.push(obj);
    }
    return momentsToRender;
  }, [calendarStartDate]);

  const cuts = useMemo(() => {
    const cuts = [];
    for (let i = 0; i <= 24 * 7; i++) {
      cuts.push({});
    }
    return cuts;
  }, []);

  return (
    <div className={cx('root')}>
      {debug && (
        <svg version="1.1" width="100%" height="6px" xmlns="http://www.w3.org/2000/svg" className={cx('debug-scale')}>
          {cuts.map((_cut, index) => (
            <line
              key={index}
              x1={`${(index * 100) / (24 * 7)}%`}
              strokeWidth={1}
              y1="0"
              x2={`${(index * 100) / (24 * 7)}%`}
              y2="6px"
              stroke="rgba(204, 204, 220, 0.65)"
            />
          ))}
        </svg>
      )}

      {momentsToRender.map((m, i) => {
        const isCurrentDay = currentDateInSelectedTimezone.isSame(m.moment, 'day');

        // const isWeekend = m.moment.day() == 0 || m.moment.day() === 6;

        return (
          <div key={i} className={cx('weekday' /* , { 'weekday--weekend': isWeekend } */)}>
            <div className={cx('weekday-title')}>
              <Text type="secondary" strong={isCurrentDay}>
                {m.moment.format('ddd D MMM')}
              </Text>
            </div>
            <div className={cx('weekday-times')}>
              {m.moments.map((mm, j) => (
                <div key={j} className={cx('weekday-time')}>
                  <div
                    className={cx('weekday-time-title', {
                      'weekday-time-title__hidden': i === 0 && j === 0,
                    })}
                  >
                    <Text type="secondary">{mm.format('HH:mm')}</Text>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
});
