import React, { ChangeEvent, useCallback } from 'react';

import { Field, Icon, Input, RadioButtonGroup } from '@grafana/ui';
import cn from 'classnames/bind';

import { ScheduleType } from 'models/schedule/schedule.types';

import styles from './SchedulesFilters.module.scss';
import { SchedulesFiltersType } from './SchedulesFilters.types';

const cx = cn.bind(styles);

interface SchedulesFiltersProps {
  value: SchedulesFiltersType;
  onChange: (filters: SchedulesFiltersType) => void;
}

const SchedulesFilters = (props: SchedulesFiltersProps) => {
  const { value, onChange } = props;

  const onSearchTermChangeCallback = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      onChange({ ...value, searchTerm: e.currentTarget.value });
    },
    [value]
  );

  const handleMineChange = useCallback(
    (mine) => {
      onChange({ ...value, mine });
    },
    [value]
  );

  const handleStatusChange = useCallback(
    (used) => {
      onChange({ ...value, used });
    },
    [value]
  );

  const handleTypeChange = useCallback(
    (type) => {
      onChange({ ...value, type });
    },
    [value]
  );

  return (
    <>
      <div className={cx('left')}>
        <Field label="Search by name">
          <Input
            autoFocus
            className={cx('search')}
            prefix={<Icon name="search" />}
            placeholder="Search..."
            value={value.searchTerm}
            onChange={onSearchTermChangeCallback}
          />
        </Field>
      </div>
      <div className={cx('right')}>
        <Field label="Mine">
          <RadioButtonGroup
            options={[
              { label: 'All', value: undefined },
              {
                label: 'Mine',
                value: true,
              },
              {
                label: 'Not mine',
                value: false,
              },
            ]}
            value={value.mine}
            onChange={handleMineChange}
          />
        </Field>
        <Field label="Status">
          <RadioButtonGroup
            options={[
              { label: 'All', value: undefined },
              {
                label: 'Used in escalations',
                value: true,
              },
              { label: 'Unused', value: false },
            ]}
            value={value.used}
            onChange={handleStatusChange}
          />
        </Field>
        <Field label="Type">
          <RadioButtonGroup
            options={[
              { label: 'All', value: undefined },
              {
                label: 'Web',
                value: ScheduleType.API,
              },
              {
                label: 'ICal',
                value: ScheduleType.Ical,
              },
              {
                label: 'API',
                value: ScheduleType.Calendar,
              },
            ]}
            value={value?.type}
            onChange={handleTypeChange}
          />
        </Field>
      </div>
    </>
  );
};

export default SchedulesFilters;
