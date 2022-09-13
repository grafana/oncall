import React, { useCallback, useEffect, useMemo, useState } from 'react';

import { SelectableValue } from '@grafana/data';
import { AsyncMultiSelect, AsyncSelect } from '@grafana/ui';
import cn from 'classnames/bind';
import { inject, observer } from 'mobx-react';

import { makeRequest } from 'network';

import styles from './RemoteSelect.module.css';

const cx = cn.bind(styles);

interface RemoteSelectProps {
  autoFocus?: boolean;
  href: string;
  value: string | string[] | number | number[] | null;
  onChange: (value: any, item: any) => void;
  fieldToShow?: string;
  getFieldToShow?: (item: any) => string;
  valueField?: string;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
  showSearch?: boolean;
  allowClear?: boolean;
  isMulti?: boolean;
  openMenuOnFocus?: boolean;
  getOptionLabel?: (item: SelectableValue) => React.ReactNode;
  showError?: boolean;
}

const RemoteSelect = inject('store')(
  observer((props: RemoteSelectProps) => {
    const {
      autoFocus,
      fieldToShow = 'display_name',
      valueField = 'value',
      isMulti = false,
      placeholder,
      className,
      value: propValue,
      onChange,
      disabled,
      href,
      showSearch = true,
      allowClear,
      getOptionLabel,
      openMenuOnFocus = true,
      showError,
    } = props;

    const [options, setOptions] = useState<SelectableValue[] | undefined>();

    const getOptions = (data: any[]) => {
      return data.map((option: any) => ({
        value: option[valueField],
        label: option[fieldToShow],
        data: option,
      }));
    };

    useEffect(() => {
      makeRequest(href, {}).then((data) => {
        setOptions(getOptions(data.results || data));
      });
    }, []);

    const loadOptionsCallback = useCallback((query: string) => {
      return makeRequest(href, { params: { search: query } }).then((data) => getOptions(data.results || data));
    }, []);

    const onChangeCallback = useCallback(
      (option) => {
        if (isMulti) {
          const values = option.map((option: SelectableValue) => option.value);
          const items = option.map((option: SelectableValue) => option.data);

          onChange(values, items);
        } else {
          onChange(option.value, option.data);
        }
      },
      [onChange, fieldToShow]
    );

    const value = useMemo(() => {
      if (isMulti) {
        return options && propValue
          ? // @ts-ignore
            propValue.map((value: string) => options.find((option) => option.value === value))
          : undefined;
      } else {
        return options ? options.find((option) => option.value === propValue) : undefined;
      }
    }, [propValue, options]);

    const Tag = isMulti ? AsyncMultiSelect : AsyncSelect;

    return (
      // @ts-ignore
      <Tag
        menuShouldPortal
        openMenuOnFocus={openMenuOnFocus}
        isClearable={allowClear}
        autoFocus={autoFocus}
        disabled={disabled}
        placeholder={placeholder}
        className={className}
        isSearchable={showSearch}
        value={value}
        onChange={onChangeCallback}
        defaultOptions={options}
        loadOptions={loadOptionsCallback}
        getOptionLabel={getOptionLabel}
        invalid={showError}
      />
    );
  })
);

export default RemoteSelect;
