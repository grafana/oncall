import React, { ChangeEvent, useCallback, useEffect, useRef } from 'react';

import { css, cx } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { Icon, Input, useStyles2 } from '@grafana/ui';

import { useDebouncedCallback } from 'utils/hooks';

interface UsersFiltersProps {
  value: any;
  onChange: (filters: any, invalidateFn: () => boolean) => void;
  className?: string;
  isLoading?: boolean;
}

const DEBOUNCE_MS = 500;

export const UsersFilters = (props: UsersFiltersProps) => {
  const styles = useStyles2(getStyles);
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
    <div className={cx(styles.root, className)}>
      <Input
        loading={isLoading}
        prefix={<Icon name="search" />}
        className={cx(styles.search, styles.control)}
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

const getStyles = (_theme: GrafanaTheme2) => {
  return {
    root: css`
      display: inline-flex;
      align-items: center;
    `,

    search: css`
      width: 300px;

      &:focus {
        width: 500px;
      }
    `,

    control: css`
      &:not(:last-child) {
        margin-right: 20px;
      }
    `,
  };
};
