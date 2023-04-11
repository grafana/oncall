import React, { ChangeEvent, useCallback } from 'react';

import { Icon, Input } from '@grafana/ui';
import cn from 'classnames/bind';

import styles from './SearchInput.module.scss';

const cx = cn.bind(styles);

interface SearchInputProps {
  value: any;
  onChange: (filters: any) => void;
  className?: string;
}

const SearchInput = (props: SearchInputProps) => {
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
        className={cx('search', 'control')}
        placeholder="Search"
        value={value.searchTerm}
        onChange={onSearchTermChangeCallback}
        suffix={<Icon name="search" />}
      />
    </div>
  );
};

export default SearchInput;
