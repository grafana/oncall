import React, { useCallback, useMemo } from 'react';

import { DateTime, dateTime } from '@grafana/data';
import { DatePickerWithInput, HorizontalGroup, TimeOfDayPicker } from '@grafana/ui';
import dayjs from 'dayjs';

import { Timezone } from 'models/timezone/timezone.types';

interface UserTooltipProps {
  value: dayjs.Dayjs;
  timezone: Timezone;
  onChange: (value: dayjs.Dayjs) => void;
  disabled?: boolean;
  minMoment?: dayjs.Dayjs;
  onFocus?: () => void;
  onBlur?: () => void;
}

const toDate = (moment: dayjs.Dayjs, timezone: Timezone) => {
  const localMoment = dayjs().tz(timezone).utcOffset() === 0 ? moment : moment.tz(timezone);

  return new Date(
    localMoment.get('year'),
    localMoment.get('month'),
    localMoment.get('date'),
    localMoment.get('hour'),
    localMoment.get('minute'),
    localMoment.get('second')
  );
};

const DateTimePicker = (props: UserTooltipProps) => {
  const { value: propValue, minMoment, timezone, onChange, disabled, onFocus, onBlur } = props;

  const value = useMemo(() => toDate(propValue, timezone), [propValue, timezone]);

  const minDate = useMemo(() => (minMoment ? toDate(minMoment, timezone) : undefined), [minMoment, timezone]);

  const handleDateChange = (newDate: Date) => {
    const localMoment = dayjs().tz(timezone).utcOffset() === 0 ? dayjs().utc() : dayjs().tz(timezone);

    const newValue = localMoment
      .set('year', newDate.getFullYear())
      .set('month', newDate.getMonth())
      .set('date', newDate.getDate())
      .set('hour', value.getHours())
      .set('minute', value.getMinutes())
      .set('second', value.getSeconds());

    onChange(newValue);
  };
  const handleTimeChange = useCallback(
    (newMoment: DateTime) => {
      const localMoment = dayjs().tz(timezone).utcOffset() === 0 ? dayjs().utc() : dayjs().tz(timezone);
      const newDate = newMoment.toDate();
      const newValue = localMoment
        .set('year', value.getFullYear())
        .set('month', value.getMonth())
        .set('date', value.getDate())
        .set('hour', newDate.getHours())
        .set('minute', newDate.getMinutes())
        .set('second', newDate.getSeconds());

      onChange(newValue);
    },
    [value]
  );

  return (
    <HorizontalGroup spacing="sm">
      <div onFocus={onFocus} onBlur={onBlur}>
        <DatePickerWithInput minDate={minDate} disabled={disabled} value={value} onChange={handleDateChange} />
      </div>
      <div onFocus={onFocus} onBlur={onBlur}>
        <TimeOfDayPicker disabled={disabled} value={dateTime(value)} onChange={handleTimeChange} />
      </div>
    </HorizontalGroup>
  );
};

export default DateTimePicker;
