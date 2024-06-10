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
      return date.set('hours', 23).toDate();
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

const getStyles = () => ({
  wrapper: css`
    display: flex;
    flex-wrap: nowrap;
    gap: 8px;
    z-index: 2;
  `,
});
