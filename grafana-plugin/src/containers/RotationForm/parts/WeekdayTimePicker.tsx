import React, { useCallback, useMemo } from 'react';

import { DateTime, dateTime, SelectableValue } from '@grafana/data';
import { Select, TimeOfDayPicker, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';

import Text from 'components/Text/Text';
import { toDate } from 'containers/RotationForm/RotationForm.helpers';
import { Timezone } from 'models/timezone/timezone.types';
import { useStore } from 'state/useStore';

import styles from 'containers/RotationForm/RotationForm.module.css';

const cx = cn.bind(styles);

interface WeekdayTimePickerProps {
  value: dayjs.Dayjs;
  timezone: Timezone;
  onWeekDayChange: (value: number) => void;
  onTimeChange: (hh: number, mm: number, ss: number) => void;
  disabled?: boolean;
  hideWeekday?: boolean;
  weekStart: string;
  error?: string[];
}

const weekdays = ['SU', 'MO', 'TU', 'WE', 'TH', 'FR', 'SA'];

const WeekdayTimePicker = (props: WeekdayTimePickerProps) => {
  const { value: propValue, timezone, hideWeekday, disabled, weekStart, onWeekDayChange, onTimeChange, error } = props;

  const { scheduleStore } = useStore();

  const value = useMemo(() => toDate(propValue, timezone), [propValue, timezone]);

  const options = useMemo(() => {
    const index = scheduleStore.byDayOptions.findIndex(
      ({ display_name }) => display_name.toLowerCase() === weekStart.toLowerCase()
    );
    return [...scheduleStore.byDayOptions.slice(index), ...scheduleStore.byDayOptions.slice(0, index)].map(
      ({ display_name, value }) => ({
        label: display_name.substring(0, 3),
        value: weekdays.findIndex((val) => val === value),
      })
    );
  }, [weekStart]);

  const handleWeekDayChange = useCallback(
    ({ value: newValue }: SelectableValue) => {
      const oldIndex = options.findIndex(({ value: optionValue }) => optionValue === value.getDay());
      const newIndex = options.findIndex(({ value: optionValue }) => optionValue === newValue);

      onWeekDayChange(newIndex - oldIndex);
    },
    [options, value]
  );

  const handleTimeChange = useCallback(
    (newMoment: DateTime) => {
      // @ts-ignore actually new newMoment has second method
      onTimeChange(newMoment.hour(), newMoment.minute(), newMoment.second());
    },
    [value]
  );

  return (
    <VerticalGroup>
      <div style={{ display: 'flex', flexWrap: 'nowrap', gap: '8px' }}>
        {!hideWeekday && (
          <div style={{ width: '58%' }} className={cx({ 'control--error': Boolean(error) })}>
            <Select options={options} onChange={handleWeekDayChange} value={value.getDay()} />
          </div>
        )}
        <div style={{ width: hideWeekday ? '100%' : '42%' }} className={cx({ 'control--error': Boolean(error) })}>
          <TimeOfDayPicker disabled={disabled} value={dateTime(value)} onChange={handleTimeChange} />
        </div>
      </div>
      {error && <Text type="danger">{error}</Text>}
    </VerticalGroup>
  );
};

export default WeekdayTimePicker;
