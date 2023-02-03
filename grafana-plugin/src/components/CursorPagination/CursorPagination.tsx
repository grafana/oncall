import React, { FC, useCallback, useEffect, useState } from 'react';

import { SelectableValue } from '@grafana/data';
import { Button, HorizontalGroup, Icon, Select } from '@grafana/ui';

import Text from 'components/Text/Text';

interface CursorPaginationProps {
  current: string;
  onChange: (cursor: string, direction: 'prev' | 'next') => void;
  itemsPerPageOptions: Array<SelectableValue<number>>;
  itemsPerPage: number;
  onChangeItemsPerPage: (value: number) => void;
  prev: string;
  next: string;
}

const CursorPagination: FC<CursorPaginationProps> = (props) => {
  const { current, onChange, prev, next, itemsPerPage, itemsPerPageOptions, onChangeItemsPerPage } = props;

  const [disabled, setDisabled] = useState<boolean>(false);

  useEffect(() => {
    setDisabled(false);
  }, [prev, next]);

  const onChangeItemsPerPageCallback = useCallback((option) => {
    setDisabled(true);
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
          onClick={() => {
            setDisabled(true);
            onChange(prev, 'prev');
          }}
          disabled={disabled || !prev}
        >
          <Icon name="angle-left" />
        </Button>
        <Text type="secondary">{current}</Text>
        <Button
          aria-label="previous"
          size="sm"
          variant="secondary"
          onClick={() => {
            setDisabled(true);
            onChange(next, 'next');
          }}
          disabled={disabled || !next}
        >
          <Icon name="angle-right" />
        </Button>
      </HorizontalGroup>
    </HorizontalGroup>
  );
};

export default CursorPagination;
