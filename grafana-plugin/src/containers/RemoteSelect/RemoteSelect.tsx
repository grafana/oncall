import React, { useCallback, useMemo, useReducer, useState } from 'react';

import { SelectableValue } from '@grafana/data';
import { AsyncMultiSelect, AsyncSelect } from '@grafana/ui';
import { inject, observer } from 'mobx-react';

import { makeRequest, isNetworkError } from 'network';
import { UserAction, generateMissingPermissionMessage } from 'utils/authorization';
import { useDebouncedCallback } from 'utils/hooks';

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
  maxMenuHeight?: number;
  requiredUserAction?: UserAction;
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
      maxMenuHeight,
      requiredUserAction,
    } = props;

    const [noOptionsMessage, setNoOptionsMessage] = useState<string>('No options found');

    const getOptions = (data: any[]): SelectableValue[] => {
      return data.map((option: any) => ({
        value: option[valueField],
        label: option[fieldToShow],
        data: option,
      }));
    };

    function mergeOptions(oldOptions: SelectableValue[], newOptions: SelectableValue[]) {
      const existingValues = oldOptions.map((o) => o.value);
      return oldOptions.concat(newOptions.filter(({ value }) => !existingValues.includes(value)));
    }

    const [options, setOptions] = useReducer(mergeOptions, []);

    const loadOptionsCallback = useDebouncedCallback(async (query: string, cb) => {
      try {
        const data = await makeRequest(href, { params: { search: query } });
        const options = getOptions(data.results || data);
        setOptions(options);

        cb(options);
      } catch (e) {
        if (isNetworkError(e) && e.response.status === 403 && requiredUserAction) {
          setNoOptionsMessage(generateMissingPermissionMessage(requiredUserAction));
        }
        cb([]);
      }
    }, 250);

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
        maxMenuHeight={maxMenuHeight}
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
        defaultOptions
        loadOptions={loadOptionsCallback}
        getOptionLabel={getOptionLabel}
        noOptionsMessage={noOptionsMessage}
        invalid={showError}
      />
    );
  })
);

export default RemoteSelect;
