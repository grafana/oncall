import React, { useCallback, useMemo } from 'react';

import { DateTime, dateTime } from '@grafana/data';
import { DatePickerWithInput, HorizontalGroup, TimeOfDayPicker, Tooltip } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';
import { Moment } from 'moment-timezone';

import { Timezone } from 'models/timezone/timezone.types';
import { getUserNotificationsSummary } from 'models/user/user.helpers';
import { User } from 'models/user/user.types';
import { useStore } from 'state/useStore';

import styles from 'containers/UserTooltip/UserTooltip.module.css';

const cx = cn.bind(styles);

interface UserTooltipProps {
  value: dayjs.Dayjs;
  timezone: Timezone;
  onChange: (value: dayjs.Dayjs) => void;
  disabled?: boolean;
  minMoment?: dayjs.Dayjs;
}

const toDate = (moment: dayjs.Dayjs) => {
  return new Date(
    moment.get('year'),
    moment.get('month'),
    moment.get('date'),
    moment.get('hour'),
    moment.get('minute'),
    moment.get('second')
  );
};

const DateTimePicker = (props: UserTooltipProps) => {
  const { value: propValue, minMoment, timezone, onChange, disabled } = props;

  const value = useMemo(() => {
    const localValue = propValue.tz(timezone);

    return toDate(localValue);
  }, [propValue, timezone]);

  const minDate = useMemo(() => (minMoment ? toDate(minMoment.tz(timezone)) : undefined), [minMoment, timezone]);

  const handleDateChange = useCallback(
    (newDate: Date) => {
      const newValue = dayjs()
        .tz(timezone)
        .set('year', newDate.getFullYear())
        .set('month', newDate.getMonth())
        .set('date', newDate.getDate())
        .set('hour', value.getHours())
        .set('minute', value.getMinutes())
        .set('second', value.getSeconds());

      onChange(newValue);
    },
    [value]
  );

  const handleTimeChange = useCallback(
    (newMoment: DateTime) => {
      const newDate = newMoment.toDate();
      const newValue = dayjs()
        .tz(timezone)
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
      <DatePickerWithInput minDate={minDate} disabled={disabled} value={value} onChange={handleDateChange} />
      <TimeOfDayPicker disabled={disabled} value={dateTime(value)} onChange={handleTimeChange} />
    </HorizontalGroup>
  );
};

export default DateTimePicker;
