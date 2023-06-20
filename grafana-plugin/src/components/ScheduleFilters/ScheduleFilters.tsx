import React, { useCallback } from 'react';

import { InlineSwitch } from '@grafana/ui';
import cn from 'classnames/bind';

import { User } from 'models/user/user.types';

import styles from './ScheduleFilters.module.scss';
import { ScheduleFiltersType } from './ScheduleFilters.types';

const cx = cn.bind(styles);

interface SchedulesFiltersProps {
  value: ScheduleFiltersType;
  currentUserPk: User['pk'];
  onChange: (filters: ScheduleFiltersType) => void;
}

const SchedulesFilters = (props: SchedulesFiltersProps) => {
  const { value, currentUserPk, onChange } = props;

  const handleShowMyShiftsOnlyClick = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const newUsers = [...value.users];

      if (event.target.checked && !value.users.includes(currentUserPk)) {
        newUsers.push(currentUserPk);
      } else {
        const index = value.users.findIndex((pk) => pk === currentUserPk);
        newUsers.splice(index, 1);
      }

      onChange({ ...value, users: newUsers });
    },
    [value]
  );

  return (
    <div className={cx('root')}>
      <InlineSwitch
        showLabel
        label="Highlight my shifts"
        value={value.users.includes(currentUserPk)}
        onChange={handleShowMyShiftsOnlyClick}
      />
    </div>
  );
};

export default SchedulesFilters;
