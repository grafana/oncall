import React from 'react';

import { css } from '@emotion/css';
import { DateTime, dateTime } from '@grafana/data';
import { DatePickerWithInput, TimeOfDayPicker, useStyles2, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';

import { Text } from 'components/Text/Text';
import { getDateForDatePicker } from 'containers/RotationForm/RotationForm.helpers';
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

export const DateTimePicker = observer(
  ({ value: propValue, onChange, disabled, onFocus, onBlur, error }: DateTimePickerProps) => {
    const styles = useStyles2(getStyles);
    const { timezoneStore } = useStore();
    const { getDateInSelectedTimezone, selectedTimezoneOffset } = timezoneStore;

    const valueInSelectedTimezone = getDateInSelectedTimezone(propValue);

    const handleDateChange = (newDate: Date) => {
      const dateInDayJS = dayjs(newDate);

      // newDate will always point to a new day in the calendar at 00:00 local timezone
      // We need to clone the date and apply only the new changes to it (year/month/date);
      // Because we're only altering the date and not the time of it

      const newDateTime = propValue
        .clone()
        .set('year', dateInDayJS.year())
        .set('month', dateInDayJS.month())
        .set('date', dateInDayJS.date());

      onChange(newDateTime);
    };

    const handleTimeChange = (timeMoment: DateTime) => {
      // Same as above, clone the date and only alter hour and minute from timeMoment
      const newDateTime = propValue.clone().set('hour', timeMoment.hour()).set('minute', timeMoment.minute());

      onChange(newDateTime);
    };

    const getTimeValueInSelectedTimezone = () => {
      const time = dateTime(valueInSelectedTimezone.format());
      time.set('hour', valueInSelectedTimezone.hour());
      time.set('minute', valueInSelectedTimezone.minute());
      time.set('second', valueInSelectedTimezone.second());
      return time;
    };

    return (
      <VerticalGroup>
        <div className={styles.wrapper}>
          <div
            onFocus={onFocus}
            onBlur={onBlur}
            style={{ width: '58%' }}
            className={cx({ 'control--error': Boolean(error) })}
          >
            <DatePickerWithInput
              open
              disabled={disabled}
              value={valueInSelectedTimezone.toDate()}
              onChange={handleDateChange}
            />
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

const getStyles = () => ({
  wrapper: css`
    display: flex;
    flex-wrap: nowrap;
    gap: 8px;
    z-index: 2;
  `,
});
