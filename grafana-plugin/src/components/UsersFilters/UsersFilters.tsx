import React, { ChangeEvent, useCallback } from 'react';

import { Icon, Input } from '@grafana/ui';
import cn from 'classnames/bind';

import styles from './UsersFilters.module.css';

const cx = cn.bind(styles);

interface UsersFiltersProps {
  searchTerm: string;
  onChange: (searchTerm: string) => void;
  className?: string;
}

const UsersFilters = (props: UsersFiltersProps) => {
  const { searchTerm = '', onChange, className } = props;

  const onSearchTermChangeCallback = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      onChange(e.currentTarget.value);
    },
    [onChange, searchTerm]
  );

  return (
    <div className={cx('root', className)}>
      <Input
        prefix={<Icon name="search" />}
        className={cx('search', 'control')}
        placeholder="Search users..."
        value={searchTerm}
        onChange={onSearchTermChangeCallback}
      />
    </div>
  );
};

export default UsersFilters;
