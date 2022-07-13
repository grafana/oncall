import React, { FC, useCallback } from 'react';

import { SelectableValue } from '@grafana/data';
import { Button, HorizontalGroup, Icon, Select } from '@grafana/ui';
import cn from 'classnames/bind';

import Text from 'components/Text/Text';

import styles from './CursorPagination.module.css';

interface CursorPaginationProps {
  current: string;
  onChange: (cursor: string, direction: 'prev' | 'next') => void;
  itemsPerPageOptions: Array<SelectableValue<number>>;
  itemsPerPage: number;
  onChangeItemsPerPage: (value: number) => void;
  prev: string;
  next: string;
}

const cx = cn.bind(styles);

const CursorPagination: FC<CursorPaginationProps> = (props) => {
  const { current, onChange, prev, next, itemsPerPage, itemsPerPageOptions, onChangeItemsPerPage } = props;

  const onChangeItemsPerPageCallback = useCallback((option) => {
    onChangeItemsPerPage(option.value);
  }, []);

  return (
    <HorizontalGroup spacing="md" justify="flex-end">
      <HorizontalGroup>
        <Text type="secondary">Items per list</Text>
        <Select
          isSearchable={false}
          options={itemsPerPageOptions}
          value={itemsPerPage}
          onChange={onChangeItemsPerPageCallback}
        />
      </HorizontalGroup>
      <HorizontalGroup>
        <Button
          aria-label="previous"
          size="sm"
          variant="secondary"
          onClick={() => onChange(prev, 'prev')}
          disabled={!prev}
        >
          <Icon name="angle-left" />
        </Button>
        <Text type="secondary">{current}</Text>
        <Button
          aria-label="previous"
          size="sm"
          variant="secondary"
          onClick={() => onChange(next, 'next')}
          disabled={!next}
        >
          <Icon name="angle-right" />
        </Button>
      </HorizontalGroup>
    </HorizontalGroup>
  );
};

export default CursorPagination;
