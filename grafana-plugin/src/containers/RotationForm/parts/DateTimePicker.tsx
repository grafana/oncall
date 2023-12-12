import React, { useMemo } from 'react';

import { DateTime, dateTimeForTimeZone } from '@grafana/data';
import { DatePickerWithInput, TimeOfDayPicker, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';

import Text from 'components/Text/Text';
import { forceCurrentDateToPreventDSTIssues, toDate } from 'containers/RotationForm/RotationForm.helpers';
import { Timezone } from 'models/timezone/timezone.types';

import styles from 'containers/RotationForm/RotationForm.module.css';

const cx = cn.bind(styles);

interface DateTimePickerProps {
  value: dayjs.Dayjs;
  timezone: Timezone;
  onChange: (value: dayjs.Dayjs) => void;
  disabled?: boolean;
  minMoment?: dayjs.Dayjs;
  onFocus?: () => void;
  onBlur?: () => void;
  error?: string[];
}

const DateTimePicker = (props: DateTimePickerProps) => {
  const { value, minMoment, timezone, onChange, disabled, onFocus, onBlur, error } = props;

  const currentDateForTimePicker = dateTimeForTimeZone(timezone, forceCurrentDateToPreventDSTIssues(value));
  const originalValue = value.toDate();

  const minDate = useMemo(() => (minMoment ? toDate(minMoment, timezone) : undefined), [minMoment, timezone]);

  const handleDateChange = (newDate: Date) => {
    const localMoment = dayjs().tz(timezone).utcOffset() === 0 ? dayjs().utc() : dayjs().tz(timezone);

    const newValue = localMoment
      .set('year', newDate.getFullYear())
      .set('month', newDate.getMonth())
      .set('date', newDate.getDate())
      .set('hour', originalValue.getHours())
      .set('minute', originalValue.getMinutes())
      .set('second', originalValue.getSeconds());

    onChange(newValue);
  };
  const handleTimeChange = (newMoment: DateTime) => {
    const localMoment = dayjs().tz(timezone).utcOffset() === 0 ? dayjs().utc() : dayjs().tz(timezone);
    const newDate = dateTimeForTimeZone(timezone, newMoment);
    const newValue = localMoment
      .set('year', originalValue.getFullYear())
      .set('month', originalValue.getMonth())
      .set('date', originalValue.getDate())
      .set('hour', newDate.hour())
      .set('minute', newDate.minute());

    onChange(newValue);
  };

  return (
    <VerticalGroup>
      <div style={{ display: 'flex', flexWrap: 'nowrap', gap: '8px' }}>
        <div
          onFocus={onFocus}
          onBlur={onBlur}
          style={{ width: '58%' }}
          className={cx({ 'control--error': Boolean(error) })}
        >
          <DatePickerWithInput
            open
            minDate={minDate}
            disabled={disabled}
            value={originalValue}
            onChange={handleDateChange}
          />
        </div>
        <div
          onFocus={onFocus}
          onBlur={onBlur}
          style={{ width: '42%' }}
          className={cx({ 'control--error': Boolean(error) })}
        >
          <TimeOfDayPicker disabled={disabled} value={currentDateForTimePicker} onChange={handleTimeChange} />
        </div>
      </div>
      {error && <Text type="danger">{error}</Text>}
    </VerticalGroup>
  );
};

export default DateTimePicker;
