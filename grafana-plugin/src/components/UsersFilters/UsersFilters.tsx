import React, { ChangeEvent, useCallback } from 'react';

import { Icon, Input } from '@grafana/ui';
import cn from 'classnames/bind';

import styles from './UsersFilters.module.css';

const cx = cn.bind(styles);

interface UsersFiltersProps {
  value: any;
  onChange: (filters: any) => void;
  className?: string;
}

const UsersFilters = (props: UsersFiltersProps) => {
  const { value = { searchTerm: '' }, onChange, className } = props;

  const onSearchTermChangeCallback = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const filters = {
        ...value,
        searchTerm: e.currentTarget.value,
      };

      onChange(filters);
    },
    [onChange, value]
  );

  return (
    <div className={cx('root', className)}>
      <Input
        prefix={<Icon name="search" />}
        className={cx('search', 'control')}
        placeholder="Search users..."
        value={value.searchTerm}
        onChange={onSearchTermChangeCallback}
      />
    </div>
  );
};

export default UsersFilters;
