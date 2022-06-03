import React, { ChangeEvent, useCallback, useMemo, useState } from 'react';

import { DatePickerWithInput, Field, HorizontalGroup, RadioButtonGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import moment from 'moment';

import { dateStringToOption, optionToDateString } from './SchedulesFilters.helpers';
import { SchedulesFiltersType } from './SchedulesFilters.types';

import styles from './SchedulesFilters.module.css';

const cx = cn.bind(styles);

interface SchedulesFiltersProps {
  value: SchedulesFiltersType;
  onChange: (filters: SchedulesFiltersType) => void;
  className?: string;
}

const SchedulesFilters = (props: SchedulesFiltersProps) => {
  const { value, onChange, className } = props;

  const handleDateChange = useCallback((date: Date) => {
    onChange({ selectedDate: moment(date).format('YYYY-MM-DD') });
  }, []);

  const option = useMemo(() => dateStringToOption(value.selectedDate), [value]);

  const handleOptionChange = useCallback((option: string) => {
    onChange({ ...value, selectedDate: optionToDateString(option) });
  }, []);

  const datePickerValue = useMemo(() => moment(value.selectedDate).toDate(), [value]);

  return (
    <div className={cx('root', className)}>
      <HorizontalGroup>
        <Field label="Filter events">
          <RadioButtonGroup
            options={[
              { value: 'today', label: 'Today' },
              { value: 'tomorrow', label: 'Tomorrow' },
              { value: 'custom', label: 'Custom' },
            ]}
            value={option}
            onChange={handleOptionChange}
          />
        </Field>
        <Field label="Date">
          <DatePickerWithInput closeOnSelect width={40} value={datePickerValue} onChange={handleDateChange} />
        </Field>
      </HorizontalGroup>
    </div>
  );
};

export default SchedulesFilters;
