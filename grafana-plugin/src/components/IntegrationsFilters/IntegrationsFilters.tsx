import React, { ChangeEvent, FC, useCallback } from 'react';

import { Icon, Input, Button } from '@grafana/ui';
import cn from 'classnames/bind';

import styles from 'components/IntegrationsFilters/IntegrationsFilters.module.css';

export interface Filters {
  searchTerm: string;
}

interface IntegrationsFiltersProps {
  value: Filters;
  onChange: (filters: Filters) => void;
}

const cx = cn.bind(styles);

const IntegrationsFilters: FC<IntegrationsFiltersProps> = (props) => {
  const { value, onChange } = props;

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

  const handleClear = useCallback(() => {
    onChange({ searchTerm: '' });
  }, [onChange]);

  return (
    <div className={cx('root', 'integrationsFilters')}>
      <Input
        autoFocus
        prefix={<Icon name="search" />}
        className={cx('search', 'control', 'searchIntegrationInput')}
        placeholder="Search integrations..."
        value={value.searchTerm}
        onChange={onSearchTermChangeCallback}
      />
      <Button variant="secondary" icon="times" onClick={handleClear} className={cx('searchIntegrationClear')}>
        Clear filters
      </Button>
    </div>
  );
};

export default IntegrationsFilters;
