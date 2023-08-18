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
  convertToUTC?: boolean;
  onChange: (value: string[]) => void;
}

function getMoments(from: string, to: string, convertToUTC: boolean) {
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
    fromMoment = (convertToUTC ? moment().utc() : moment()).hour(fh).minute(fm).second(0).local();

    const [th, tm] = to.split(':').map(Number);
    toMoment = (convertToUTC ? moment().utc() : moment()).hour(th).minute(tm).second(0).local();
  }

  return [fromMoment, toMoment];
}

function getRangeStrings(from: moment.Moment, to: moment.Moment, convertToUTC: boolean) {
  const fromString = (convertToUTC ? from.clone().utc() : from.clone()).format('HH:mm:00');
  const toString = (convertToUTC ? to.clone().utc() : to.clone()).format('HH:mm:00');

  return [fromString, toString];
}

const TimeRange = (props: TimeRangeProps) => {
  const { className, from: f, to: t, onChange, disabled, convertToUTC = true } = props;

  // @ts-ignore
  const [from, setFrom] = useState<moment.Moment>(getMoments(f, t, convertToUTC)[0]);
  // @ts-ignore
  const [to, setTo] = useState<moment.Moment>(getMoments(f, t, convertToUTC)[1]);

  useEffect(() => {
    if (!f || !t) {
      onChange(getRangeStrings(from, to, convertToUTC));
    }
  }, []);

  const handleChangeFrom = useCallback(
    (value: moment.Moment) => {
      setFrom(value);

      if (value.isSame(to, 'minute')) {
        const newTo = to.subtract(5, 'minute');
        setTo(newTo);
        onChange(getRangeStrings(value, newTo, convertToUTC));
      } else {
        onChange(getRangeStrings(value, to, convertToUTC));
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
        onChange(getRangeStrings(newFrom, value, convertToUTC));
      } else {
        onChange(getRangeStrings(from, value, convertToUTC));
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
