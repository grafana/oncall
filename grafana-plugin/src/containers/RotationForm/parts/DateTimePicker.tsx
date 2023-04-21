import React, { useCallback, useMemo } from 'react';

import { DateTime, dateTime } from '@grafana/data';
import { DatePickerWithInput, TimeOfDayPicker } from '@grafana/ui';
import dayjs from 'dayjs';

import { toDate } from 'containers/RotationForm/RotationForm.helpers';
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
    <div style={{ display: 'flex', flexWrap: 'nowrap', gap: '8px' }}>
      <div onFocus={onFocus} onBlur={onBlur} style={{ width: '58%' }}>
        <DatePickerWithInput open minDate={minDate} disabled={disabled} value={value} onChange={handleDateChange} />
      </div>
      <div onFocus={onFocus} onBlur={onBlur} style={{ width: '42%' }}>
        <TimeOfDayPicker disabled={disabled} value={dateTime(value)} onChange={handleTimeChange} />
      </div>
    </div>
  );
};

export default DateTimePicker;
