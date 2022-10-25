import React, { ChangeEvent, useCallback } from 'react';

import { Checkbox, HorizontalGroup, Icon, Input } from '@grafana/ui';
import cn from 'classnames/bind';

import { UserRole } from 'models/user/user.types';

import styles from './UsersFilters.module.css';

const cx = cn.bind(styles);

interface UsersFiltersProps {
  value: any;
  onChange: (filters: any) => void;
  className?: string;
}

const roleOptions = [
  { label: 'Admin', value: UserRole.ADMIN },
  { label: 'Editor', value: UserRole.EDITOR },
  { label: 'Viewer', value: UserRole.VIEWER },
];

const UsersFilters = (props: UsersFiltersProps) => {
  const { value = { searchTerm: '' }, onChange, className } = props;

  const onChangeRolesCallback = useCallback(
    (role: UserRole) => {
      return (event: ChangeEvent<HTMLInputElement>) => {
        const checked = event.target.checked;
        const roles = [...value.roles];

        if (checked && !roles.includes(role)) {
          roles.push(role);
        } else if (!checked && roles.includes(role)) {
          const index = roles.indexOf(role);
          roles.splice(index, 1);
        }

        onChange({
          ...value,
          roles,
        });
      };
    },
    [value]
  );

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
      <HorizontalGroup>
        {roleOptions.map((option) => (
          <Checkbox
            key={option.value}
            value={value.roles.includes(option.value)}
            label={option.label}
            onChange={onChangeRolesCallback(option.value)}
          />
        ))}
      </HorizontalGroup>
    </div>
  );
};

export default UsersFilters;
