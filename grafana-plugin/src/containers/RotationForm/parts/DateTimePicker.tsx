import React from 'react';

import { DateTime, dateTime } from '@grafana/data';
import { DatePickerWithInput, TimeOfDayPicker, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';

import Text from 'components/Text/Text';
import { useStore } from 'state/useStore';

import styles from 'containers/RotationForm/RotationForm.module.css';

const cx = cn.bind(styles);

interface DateTimePickerProps {
  value: dayjs.Dayjs;
  onChange: (value: dayjs.Dayjs) => void;
  disabled?: boolean;
  onFocus?: () => void;
  onBlur?: () => void;
  error?: string[];
}

const DateTimePicker = observer(
  ({ value: propValue, onChange, disabled, onFocus, onBlur, error }: DateTimePickerProps) => {
    const {
      timezoneStore: { getDateInSelectedTimezone },
    } = useStore();
    const valueInSelectedTimezone = getDateInSelectedTimezone(propValue);
    const valueAsDate = valueInSelectedTimezone.toDate();

    const handleDateChange = (newDate: Date) => {
      const localMoment = getDateInSelectedTimezone(dayjs(newDate));
      const newValue = localMoment
        .set('year', newDate.getFullYear())
        .set('month', newDate.getMonth())
        .set('date', newDate.getDate())
        .set('hour', valueAsDate.getHours())
        .set('minute', valueAsDate.getMinutes())
        .set('second', valueAsDate.getSeconds());

      onChange(newValue);
    };
    const handleTimeChange = (newMoment: DateTime) => {
      const selectedHour = newMoment.hour();
      const selectedMinute = newMoment.minute();
      const newValue = valueInSelectedTimezone.set('hour', selectedHour).set('minute', selectedMinute);

      onChange(newValue);
    };

    const getTimeValueInSelectedTimezone = () => {
      const time = dateTime(valueInSelectedTimezone.format());
      time.set('hour', valueInSelectedTimezone.hour());
      time.set('minute', valueInSelectedTimezone.minute());
      time.set('second', valueInSelectedTimezone.second());
      return time;
    };

    const getDateForDatePicker = () => {
      const date = new Date();
      date.setFullYear(valueInSelectedTimezone.year());
      date.setMonth(valueInSelectedTimezone.month());
      date.setDate(valueInSelectedTimezone.date());
      date.setHours(valueInSelectedTimezone.hour());
      date.setMinutes(valueInSelectedTimezone.minute());
      date.setSeconds(valueInSelectedTimezone.second());
      return date;
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
            <DatePickerWithInput open disabled={disabled} value={getDateForDatePicker()} onChange={handleDateChange} />
          </div>
          <div
            onFocus={onFocus}
            onBlur={onBlur}
            style={{ width: '42%' }}
            className={cx({ 'control--error': Boolean(error) })}
            data-testid="date-time-picker"
          >
            <TimeOfDayPicker disabled={disabled} value={getTimeValueInSelectedTimezone()} onChange={handleTimeChange} />
          </div>
        </div>
        {error && <Text type="danger">{error}</Text>}
      </VerticalGroup>
    );
  }
);

export default DateTimePicker;
