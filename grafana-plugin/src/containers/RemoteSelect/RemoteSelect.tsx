import React, { useCallback, useEffect, useMemo, useState } from 'react';

import { SelectableValue } from '@grafana/data';
import { AsyncMultiSelect, AsyncSelect } from '@grafana/ui';
import cn from 'classnames/bind';
import { get } from 'lodash-es';
import { inject, observer } from 'mobx-react';
import qs from 'query-string';
import Emoji from 'react-emoji-render';
import { debounce } from 'throttle-debounce';

import { API_PROXY_PREFIX, makeRequest } from 'network';
import { SelectOption } from 'state/types';

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
  getOptionLabel?: (item: SelectableValue) => React.ReactNode;
}

const RemoteSelect = inject('store')(
  observer((props: RemoteSelectProps) => {
    const {
      autoFocus,
      fieldToShow = 'display_name',
      getFieldToShow,
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
        openMenuOnFocus
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
      />
    );
  })
);

export default RemoteSelect;
