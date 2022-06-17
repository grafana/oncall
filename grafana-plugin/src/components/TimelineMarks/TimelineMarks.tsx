import React, { FC, useMemo } from 'react';
import cn from 'classnames/bind';

import styles from './TimelineMarks.module.css';
import * as dayjs from 'dayjs';

interface TimelineMarksProps {
  hideTimeMarks: boolean;
  startMoment: dayjs.Dayjs;
}

const cx = cn.bind(styles);

const TimelineMarks: FC<TimelineMarksProps> = (props) => {
  const { hideTimeMarks, startMoment } = props;

  const momentsToRender = useMemo(() => {
    const hoursToSplit = 12;

    const momentsToRender = [];
    const jLimit = 24 / hoursToSplit;

    for (let i = 0; i < 7; i++) {
      const d = dayjs(startMoment).utc().add(i, 'days');
      const obj = { moment: d, moments: [] };
      for (let j = 0; j < jLimit; j++) {
        const m = dayjs(d)
          .utc()
          .add(j * hoursToSplit, 'hour');
        obj.moments.push(m);
      }
      momentsToRender.push(obj);
    }
    return momentsToRender;
  }, [startMoment]);

  return (
    <div className={cx('root')}>
      {momentsToRender.map((m, i) => {
        return (
          <div key={i} className={cx('weekday')}>
            <div className={cx('weekday-title')}>
              {m.moment.format('DD MMM')}
            </div>
            <div className={cx('weekday-times')}>
              {m.moments.map((mm, j) => (
                <div key={j} className={cx('weekday-time')}>
                  <div
                    className={cx('weekday-time-title', {
                      'weekday-time-title__hidden': i == 0 && j == 0,
                    })}
                  >
                    {mm.format('HH:mm')}
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
