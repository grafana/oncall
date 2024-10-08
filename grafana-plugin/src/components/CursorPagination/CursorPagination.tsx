import React, { FC, useCallback, useEffect, useState } from 'react';

import { css } from '@emotion/css';
import { SelectableValue } from '@grafana/data';
import { Button, Icon, Select, Stack } from '@grafana/ui';
import { StackSize } from 'helpers/consts';

import { Text } from 'components/Text/Text';

interface CursorPaginationProps {
  current: string;
  onChange: (cursor: string, direction: 'prev' | 'next') => void;
  itemsPerPageOptions: Array<SelectableValue<number>>;
  itemsPerPage: number;
  onChangeItemsPerPage: (value: number) => void;
  prev: string;
  next: string;
}

export const CursorPagination: FC<CursorPaginationProps> = (props) => {
  const { current, onChange, prev, next, itemsPerPage, itemsPerPageOptions, onChangeItemsPerPage } = props;

  const [disabled, setDisabled] = useState<boolean>(false);

  useEffect(() => {
    setDisabled(false);
  }, [prev, next]);

  const onChangeItemsPerPageCallback = useCallback((option: SelectableValue) => {
    setDisabled(true);
    onChangeItemsPerPage(option.value);
  }, []);

  return (
    <Stack gap={StackSize.xs} justifyContent="flex-end">
      <Stack gap={StackSize.xs} alignItems="center">
        <Text
          type="secondary"
          className={css`
            width: 120px;
          `}
        >
          Items per list
        </Text>
        <Select
          className={css`
            max-width: 75px;
          `}
          isSearchable={false}
          options={itemsPerPageOptions}
          value={itemsPerPage}
          onChange={onChangeItemsPerPageCallback}
        />
      </Stack>
      <Stack gap={StackSize.xs} alignItems="center">
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
      </Stack>
    </Stack>
  );
};
