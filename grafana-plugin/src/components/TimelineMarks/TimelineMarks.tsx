import React, { FC, useMemo } from 'react';

import cn from 'classnames/bind';
import dayjs from 'dayjs';

import Text from 'components/Text/Text';

import styles from './TimelineMarks.module.css';

interface TimelineMarksProps {
  startMoment: dayjs.Dayjs;
  debug?: boolean;
}

const cx = cn.bind(styles);

const TimelineMarks: FC<TimelineMarksProps> = (props) => {
  const { startMoment, debug } = props;

  const momentsToRender = useMemo(() => {
    const hoursToSplit = 12;

    const momentsToRender = [];
    const jLimit = 24 / hoursToSplit;

    for (let i = 0; i < 7; i++) {
      const d = dayjs(startMoment).add(i, 'days');
      const obj = { moment: d, moments: [] };
      for (let j = 0; j < jLimit; j++) {
        const m = dayjs(d).add(j * hoursToSplit, 'hour');
        obj.moments.push(m);
      }
      momentsToRender.push(obj);
    }
    return momentsToRender;
  }, [startMoment]);

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
          {cuts.map((cut, index) => (
            <line
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
        return (
          <div key={i} className={cx('weekday')}>
            <div className={cx('weekday-title')}>
              <Text type="secondary">{m.moment.format('ddd D MMM')}</Text>
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
};

export default TimelineMarks;
