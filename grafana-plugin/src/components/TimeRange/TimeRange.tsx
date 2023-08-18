import React, { useCallback, useEffect, useMemo, useState } from 'react';

import { HorizontalGroup, TimeOfDayPicker } from '@grafana/ui';
import cn from 'classnames/bind';
import moment from 'moment-timezone';

import styles from './TimeRange.module.css';

const cx = cn.bind(styles);

interface TimeRangeProps {
  className: string;
  from: string | null;
  to: string | null;
  disabled?: boolean;
  onChange: (value: string[]) => void;
}

function getMoments(from: string, to: string) {
  let fromMoment: moment.Moment;
  let toMoment: moment.Moment;

  if (!from || !to) {
    fromMoment = moment().startOf('hour');
    toMoment = fromMoment.clone().add(8, 'hour');

    if (!toMoment.isSame(fromMoment, 'day')) {
      toMoment.subtract(1, 'day');
    }
  } else {
    const [fh, fm] = from.split(':').map(Number);
    fromMoment = moment().hour(fh).minute(fm).second(0).local();

    const [th, tm] = to.split(':').map(Number);
    toMoment = moment().hour(th).minute(tm).second(0).local();
  }

  return [fromMoment, toMoment];
}

function getRangeStrings(from: moment.Moment, to: moment.Moment) {
  const fromString = from.clone().format('HH:mm:00');
  const toString = to.clone().format('HH:mm:00');

  return [fromString, toString];
}

const TimeRange = (props: TimeRangeProps) => {
  const { className, from: f, to: t, onChange, disabled } = props;

  const [from, setFrom] = useState<moment.Moment>(getMoments(f, t)[0]);
  const [to, setTo] = useState<moment.Moment>(getMoments(f, t)[1]);

  useEffect(() => {
    if (!f || !t) {
      onChange(getRangeStrings(from, to));
    }
  }, []);

  const handleChangeFrom = useCallback(
    (value: moment.Moment) => {
      setFrom(value);

      if (value.isSame(to, 'minute')) {
        const newTo = to.subtract(5, 'minute');
        setTo(newTo);
        onChange(getRangeStrings(value, newTo));
      } else {
        onChange(getRangeStrings(value, to));
      }
    },
    [to]
  );

  const handleChangeTo = useCallback(
    (value: moment.Moment) => {
      setTo(value);

      if (value.isSame(from, 'minute')) {
        const newFrom = from.add(5, 'minute');
        setFrom(newFrom);
        onChange(getRangeStrings(newFrom, value));
      } else {
        onChange(getRangeStrings(from, value));
      }
    },
    [from]
  );

  const showNextDayTip = useMemo(() => to.isBefore(from), [from, to]);

  return (
    <div className={cx('root', className)}>
      <HorizontalGroup wrap>
        {/* @ts-ignore actually TimeOfDayPicker uses Moment objects */}
        <TimeOfDayPicker disabled={disabled} value={from} minuteStep={5} onChange={handleChangeFrom} />
        to
        {/* @ts-ignore actually TimeOfDayPicker uses Moment objects */}
        <TimeOfDayPicker disabled={disabled} value={to} minuteStep={5} onChange={handleChangeTo} />
        {showNextDayTip && 'next day'}
      </HorizontalGroup>
    </div>
  );
};

export default TimeRange;
