import React, { ReactElement, useCallback, useEffect } from 'react';

import { SelectableValue } from '@grafana/data';
import { AsyncMultiSelect, AsyncSelect } from '@grafana/ui';
import cn from 'classnames/bind';
import { get, isNil } from 'lodash-es';
import { observer } from 'mobx-react';

import { useDebouncedCallback } from 'utils/hooks';

import styles from './GSelect.module.scss';

const cx = cn.bind(styles);

interface GSelectProps<Item> {
  items: {
    [key: string]: Item;
  };
  fetchItemsFn: (query?: string) => Promise<Item[] | void>;
  fetchItemFn?: (id: string) => Promise<Item | void>;
  getSearchResult: (query?: string) => Item[] | { page_size: number; count: number; results: Item[] };
  placeholder: string;
  isLoading?: boolean;
  value?: string | string[] | null;
  defaultValue?: string | string[] | null;
  onChange: (value: string, item: any) => void;
  autoFocus?: boolean;
  defaultOpen?: boolean;
  disabled?: boolean;
  className?: string;
  displayField?: string;
  valueField?: string;
  showSearch?: boolean;
  allowClear?: boolean;
  isMulti?: boolean;
  showWarningIfEmptyValue?: boolean;
  showError?: boolean;
  nullItemName?: string;
  filterOptions?: (id: any) => boolean;
  dropdownRender?: (menu: ReactElement) => ReactElement;
  getOptionLabel?: <T>(item: SelectableValue<T>) => React.ReactNode;
  getDescription?: (item: any) => React.ReactNode;
  openMenuOnFocus?: boolean;
  width?: number | 'auto';
  icon?: string;
}

export const GSelect = observer(<Item,>(props: GSelectProps<Item>) => {
  const {
    autoFocus,
    showSearch = false,
    allowClear = false,
    isLoading,
    defaultOpen,
    placeholder,
    className,
    value,
    defaultValue,
    onChange,
    disabled,
    showError,
    displayField = 'display_name',
    valueField = 'id',
    isMulti = false,
    getOptionLabel,
    showWarningIfEmptyValue = false,
    getDescription,
    filterOptions,
    width = null,
    icon = null,
    items: propItems,
    fetchItemsFn,
    fetchItemFn,
    getSearchResult,
  } = props;

  const onChangeCallback = useCallback(
    (option) => {
      if (isMulti) {
        const values = option.map((option: SelectableValue) => option.value);
        const items = option.map((option: SelectableValue) => propItems[option.value]);

        onChange(values, items);
      } else {
        if (option) {
          const id = option.value;
          const item = propItems[id];
          onChange(id, item);
        } else {
          onChange(null, null);
        }
      }
    },
    [propItems, onChange]
  );

  const loadOptions = useDebouncedCallback((query: string, cb) => {
    fetchItemsFn(query).then(() => {
      const searchResult = getSearchResult(query);
      // TODO: we need to unify interface of search results to get rid of ts-ignore
      // @ts-ignore
      let items = Array.isArray(searchResult.results) ? searchResult.results : searchResult;
      if (filterOptions) {
        items = items.filter((opt: any) => filterOptions(opt[valueField]));
      }
      const options = items.map((item: any) => ({
        value: item[valueField],
        label: get(item, displayField),
        imgUrl: item.avatar_url,
        description: getDescription && getDescription(item),
      }));
      cb(options);
    });
  }, 250);

  const values = isMulti
    ? (value ? (value as string[]) : [])
        .filter((id) => id in propItems)
        .map((id: string) => ({
          value: id,
          label: get(propItems[id], displayField),
          description: getDescription && getDescription(propItems[id]),
        }))
    : propItems[value as string]
    ? {
        value,
        label: get(propItems[value as string], displayField) ? get(propItems[value as string], displayField) : 'hidden',
        description: getDescription && getDescription(propItems[value as string]),
      }
    : value;

  useEffect(() => {
    const values = isMulti ? value : [value];

    (values ? (values as string[]) : []).forEach((value: string) => {
      if (!isNil(value) && !propItems[value] && fetchItemFn) {
        fetchItemFn(value);
      }
    });
  }, [value]);

  const Tag = isMulti ? AsyncMultiSelect : AsyncSelect;

  return (
    <div className={cx('root', className)}>
      <Tag
        autoFocus={autoFocus}
        isSearchable={showSearch}
        isClearable={allowClear}
        placeholder={placeholder}
        openMenuOnFocus={defaultOpen}
        disabled={disabled}
        menuShouldPortal
        onChange={onChangeCallback}
        defaultOptions={!disabled}
        loadOptions={loadOptions}
        isLoading={isLoading}
        // @ts-ignore
        value={values}
        defaultValue={defaultValue}
        loadingMessage={`Loading...`}
        noOptionsMessage={`Not found`}
        getOptionLabel={getOptionLabel}
        invalid={showError || (showWarningIfEmptyValue && !value)}
        width={width}
        icon={icon}
      />
    </div>
  );
});
