import React, { FC, useMemo } from 'react';

import { cx } from '@emotion/css';
import { useStyles2 } from '@grafana/ui';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';

import { Text } from 'components/Text/Text';
import { scheduleViewToDaysInOneRow } from 'models/schedule/schedule.helpers';
import { ScheduleView } from 'models/schedule/schedule.types';
import { useStore } from 'state/useStore';

import { getTimelineMarksStyles } from './TimelineMarks.styles';

interface TimelineMarksProps {
  debug?: boolean;
  startDate?: dayjs.Dayjs;
  withBorderBottom?: boolean;
  scheduleView?: ScheduleView;
}

export const TimelineMarks: FC<TimelineMarksProps> = observer((props) => {
  const {
    timezoneStore: { currentDateInSelectedTimezone, calendarStartDate },
    scheduleStore: { scheduleView: storeScheduleView },
  } = useStore();
  const { debug, startDate: propsStartDate, withBorderBottom = false, scheduleView: propsScheduleView } = props;

  const styles = useStyles2(getTimelineMarksStyles);

  const startDate = propsStartDate || calendarStartDate;
  const scheduleView = propsScheduleView || storeScheduleView;

  const days = scheduleViewToDaysInOneRow[scheduleView];

  const momentsToRender = useMemo(() => {
    const hoursToSplit = 12;

    const momentsToRender = [];
    const jLimit = 24 / hoursToSplit;

    for (let i = 0; i < days; i++) {
      const d = dayjs(startDate).add(i, 'days');
      const obj = { moment: d, moments: [] };
      for (let j = 0; j < jLimit; j++) {
        const m = dayjs(d).add(j * hoursToSplit, 'hour');
        obj.moments.push(m);
      }
      momentsToRender.push(obj);
    }
    return momentsToRender;
  }, [startDate, days]);

  const cuts = useMemo(() => {
    const cuts = [];
    for (let i = 0; i <= 24 * days; i++) {
      cuts.push({});
    }
    return cuts;
  }, [days]);

  return (
    <div className={cx(styles.root, { [styles.rootBorderBottom]: withBorderBottom })}>
      {debug && (
        <svg version="1.1" width="100%" height="6px" xmlns="http://www.w3.org/2000/svg" className={styles.debugScale}>
          {cuts.map((_cut, index) => (
            <line
              key={index}
              x1={`${(index * 100) / (24 * days)}%`}
              strokeWidth={1}
              y1="0"
              x2={`${(index * 100) / (24 * days)}%`}
              y2="6px"
              stroke="rgba(204, 204, 220, 0.65)"
            />
          ))}
        </svg>
      )}

      {momentsToRender.map((m, i) => {
        const isCurrentDay = currentDateInSelectedTimezone.isSame(m.moment, 'day');
        const isWeekend = m.moment.day() === 0 || m.moment.day() === 6;

        return (
          <div
            key={i}
            data-testid="schedule-weekday"
            className={cx(styles.weekday, { [styles.weekdayEnd]: isWeekend })}
            style={{ width: `${100 / days}%` }}
          >
            <div className={styles.weekdayTitle}>
              <Text type={isCurrentDay ? 'primary' : 'secondary'}>
                {m.moment.date() === 1 ? m.moment.format('ddd D MMM') : m.moment.format('ddd D')}
              </Text>
            </div>
          </div>
        );
      })}
    </div>
  );
});
