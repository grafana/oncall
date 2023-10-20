import React, { ChangeEvent, useCallback, useEffect, useRef } from 'react';

import { Icon, Input } from '@grafana/ui';
import cn from 'classnames/bind';

import styles from './UsersFilters.module.css';
import { useDebouncedCallback } from 'utils/hooks';

const cx = cn.bind(styles);

interface UsersFiltersProps {
  value: any;
  onChange: (filters: any, invalidateFn: () => boolean) => void;
  className?: string;
  isLoading?: boolean;
}

const DEBOUNCE_MS = 500;

const UsersFilters = (props: UsersFiltersProps) => {
  const { value = { searchTerm: '' }, onChange: onChangeProp, className, isLoading } = props;

  // useRef instead of useState so that we don't get into closure when checking for last id
  const lastRequestId = useRef<string>(undefined);

  const onChange = useCallback(
    (filters: any) => {
      const currentRequestId = getNewRequestId();
      lastRequestId.current = currentRequestId;

      onChangeProp(filters, () => {
        // This will ensure that only the newest request will get to update the store data
        return lastRequestId.current && currentRequestId !== lastRequestId.current;
      });
    },
    [onChangeProp]
  );

  const debouncedOnChange = useDebouncedCallback(onChange, DEBOUNCE_MS);

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

  useEffect(() => {
    debouncedOnChange({
      ...value,
      searchTerm: '',
    });
  }, []);

  return (
    <div className={cx('root', className)}>
      <Input
        loading={isLoading}
        prefix={<Icon name="search" />}
        className={cx('search', 'control')}
        placeholder="Search users..."
        value={value.searchTerm}
        onChange={onSearchTermChangeCallback}
        data-testid="search-users"
      />
    </div>
  );

  function getNewRequestId() {
    return Math.random().toString(36).slice(-6);
  }
};

export default UsersFilters;
