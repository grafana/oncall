import React, { ReactElement, useCallback, useEffect } from 'react';

import { SelectableValue } from '@grafana/data';
import { AsyncMultiSelect, AsyncSelect } from '@grafana/ui';
import cn from 'classnames/bind';
import { get, isNil } from 'lodash-es';
import { observer } from 'mobx-react';

import { useStore } from 'state/useStore';

import styles from './GSelect.module.css';
// import { debounce } from 'lodash';

const cx = cn.bind(styles);

interface GSelectProps {
  placeholder: string;
  value?: string | string[] | null;
  defaultValue?: string | string[] | null;
  onChange: (value: string, item: any) => void;
  modelName: string;
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

const GSelect = observer((props: GSelectProps) => {
  const {
    autoFocus,
    showSearch = false,
    allowClear = false,
    defaultOpen,
    placeholder,
    className,
    value,
    defaultValue,
    onChange,
    disabled,
    showError,
    modelName,
    displayField = 'display_name',
    valueField = 'id',
    isMulti = false,
    getOptionLabel,
    showWarningIfEmptyValue = false,
    getDescription,
    filterOptions,
    width = null,
    icon = null,
  } = props;

  const store = useStore();
  const model = (store as any)[modelName];

  const onChangeCallback = useCallback(
    (option) => {
      if (isMulti) {
        const values = option.map((option: SelectableValue) => option.value);
        const items = option.map((option: SelectableValue) => model.items[option.value]);

        onChange(values, items);
      } else {
        if (option) {
          const id = option.value;
          const item = model.items[id];
          onChange(id, item);
        } else {
          onChange(null, null);
        }
      }
    },
    [model, onChange]
  );

  /**
   * without debouncing this function when search is available
   * we risk hammering the API endpoint for every single key stroke
   * some context on 250ms as the choice here - https://stackoverflow.com/a/44755058/3902555
   */
  const loadOptions = (query: string) => {
    return model.updateItems(query).then(() => {
      const searchResult = model.getSearchResult(query);
      let items = Array.isArray(searchResult.results) ? searchResult.results : searchResult;
      if (filterOptions) {
        items = items.filter((opt: any) => filterOptions(opt[valueField]));
      }

      return items.map((item: any) => ({
        value: item[valueField],
        label: get(item, displayField),
        imgUrl: item.avatar_url,
        description: getDescription && getDescription(item),
      }));
    });
  };

  // TODO: why doesn't this work properly?
  // const loadOptions = debounce(_loadOptions, showSearch ? 250 : 0);

  const values = isMulti
    ? (value ? (value as string[]) : [])
        .filter((id) => id in model.items)
        .map((id: string) => ({
          value: id,
          label: get(model.items[id], displayField),
          description: getDescription && getDescription(model.items[id]),
        }))
    : model.items[value as string]
    ? {
        value,
        label: get(model.items[value as string], displayField)
          ? get(model.items[value as string], displayField)
          : 'hidden',
        description: getDescription && getDescription(model.items[value as string]),
      }
    : value;

  useEffect(() => {
    const values = isMulti ? value : [value];

    (values ? (values as string[]) : []).forEach((value: string) => {
      if (!isNil(value) && !model.items[value] && model.updateItem) {
        model.updateItem(value, true);
      }
    });
  }, [value]);

  const Tag = isMulti ? AsyncMultiSelect : AsyncSelect;

  return (
    <div className={cx('root', className)}>
      {/*@ts-ignore*/}
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

export default GSelect;
