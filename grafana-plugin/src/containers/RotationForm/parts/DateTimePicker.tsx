import React from 'react';

import { css } from '@emotion/css';
import { DateTime, dateTime } from '@grafana/data';
import { DatePickerWithInput, TimeOfDayPicker, useStyles2, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';

import { Text } from 'components/Text/Text';
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
    const { selectedTimezoneOffset, getDateInSelectedTimezone } = timezoneStore;

    const valueInSelectedTimezone = getDateInSelectedTimezone(propValue);

    const handleDateChange = (value: Date) => {
      const newDate = dayjs(value)
        .utcOffset(selectedTimezoneOffset)
        .set('date', 1)
        .set('months', value.getMonth())
        .set('date', value.getDate())
        .set('hours', propValue.hour())
        .set('minutes', propValue.minute())
        .set('second', 0)
        .set('milliseconds', 0);

      onChange(newDate);
    };

    const handleTimeChange = (timeMoment: DateTime) => {
      const newDate = propValue.set('hour', timeMoment.hour()).set('minute', timeMoment.minute());

      onChange(newDate);
    };

    const getTimeValueInSelectedTimezone = () => {
      const time = dateTime(valueInSelectedTimezone.format());
      time.set('hour', valueInSelectedTimezone.hour());
      time.set('minute', valueInSelectedTimezone.minute());
      time.set('second', valueInSelectedTimezone.second());
      return time;
    };

    const forceConvertToDateWithOffset = (date: dayjs.Dayjs) => {
      // Since the date selector only cares about the date being displayed and is not tied to time as well
      // We make sure the date we pass won't be converted to the day before or day after due to DST
      // E.g. If the offset is UTC+3 and we want to set the datetime to 00:00 in a month where DST changes
      // We would actually go back 1 day (1 hour), which is not the desired result

      const formattedDate = getFormattedDateDDMMYYYY(date.toDate());
      const formattedDayMoment = date.format('DD/MM/YYYY');

      let resultDate = date;
      if (formattedDate !== formattedDayMoment) {
        resultDate = resultDate.set('hours', Math.abs(selectedTimezoneOffset / 60));
      }

      return resultDate.toDate();
    };

    // console.log('Converted date is ' + forceConvertToDateWithOffset(valueInSelectedTimezone));

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
              value={forceConvertToDateWithOffset(valueInSelectedTimezone)}
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

// TODO: Move to date helpers/util
export const getFormattedDateDDMMYYYY = (date: Date) => {
  const year = date.getFullYear();
  const month = (1 + date.getMonth()).toString().padStart(2, '0');
  const day = date.getDate().toString().padStart(2, '0');

  return day + '/' + month + '/' + year;
};

const getStyles = () => ({
  wrapper: css`
    display: flex;
    flex-wrap: nowrap;
    gap: 8px;
    z-index: 2;
  `,
});
