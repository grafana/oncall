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

  const currentDateTime = dateTimeForTimeZone(timezone, forceCurrentDateToPreventDSTIssues(value));
  const currentDate = currentDateTime.toDate();

  const minDate = useMemo(() => (minMoment ? toDate(minMoment, timezone) : undefined), [minMoment, timezone]);

  const handleDateChange = (newDate: Date) => {
    const localMoment = dayjs().tz(timezone).utcOffset() === 0 ? dayjs().utc() : dayjs().tz(timezone);

    const newValue = localMoment
      .set('year', newDate.getFullYear())
      .set('month', newDate.getMonth())
      .set('date', newDate.getDate())
      .set('hour', currentDate.getHours())
      .set('minute', currentDate.getMinutes())
      .set('second', currentDate.getSeconds());

    onChange(newValue);
  };
  const handleTimeChange = (newMoment: DateTime) => {
    const localMoment = dayjs().tz(timezone).utcOffset() === 0 ? dayjs().utc() : dayjs().tz(timezone);
    const newDate = dateTimeForTimeZone(timezone, newMoment);
    const newValue = localMoment
      .set('year', currentDate.getFullYear())
      .set('month', currentDate.getMonth())
      .set('date', currentDate.getDate())
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
            value={currentDate}
            onChange={handleDateChange}
          />
        </div>
        <div
          onFocus={onFocus}
          onBlur={onBlur}
          style={{ width: '42%' }}
          className={cx({ 'control--error': Boolean(error) })}
        >
          <TimeOfDayPicker disabled={disabled} value={currentDateTime} onChange={handleTimeChange} />
        </div>
      </div>
      {error && <Text type="danger">{error}</Text>}
    </VerticalGroup>
  );
};

export default DateTimePicker;
