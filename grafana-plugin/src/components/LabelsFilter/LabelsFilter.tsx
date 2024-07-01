import React, { FC, useCallback, useMemo, useState } from 'react';

import { AsyncMultiSelect } from '@grafana/ui';

interface Value {
  key: { [labelField: string]: any };
  value: { [labelField: string]: any };
}

interface LabelsFilterProps {
  autoFocus: boolean;
  labelField: string;
  onLoadOptions: (search: string) => Promise<any>;
  value: Value[];
  onChange: (value: Value[]) => void;
}

export const LabelsFilterComponent: FC<LabelsFilterProps> = (props) => {
  const { autoFocus, value: propsValue, labelField: FieldName = 'name', onLoadOptions, onChange } = props;

  const [search, setSearch] = useState('');

  const handleChange = useCallback((value) => {
    onChange(value.map((v) => v.data));
  }, []);

  const handleLoadOptions = async (search) => {
    const options = await onLoadOptions(search);
    return options.map((v) => ({
      label: `${v.key[FieldName]} : ${v.value[FieldName]}`,
      value: `${v.key[FieldName]} : ${v.value[FieldName]}`,
      data: v,
    }));
  };

  const value = useMemo(
    () =>
      propsValue.map((v) => ({
        label: `${v.key[FieldName]} : ${v.value[FieldName]}`,
        value: `${v.key[FieldName]} : ${v.value[FieldName]}`,
        data: v,
      })),
    [propsValue]
  );

  return (
    <AsyncMultiSelect
      autoFocus={autoFocus}
      openMenuOnFocus
      loadOptions={handleLoadOptions}
      value={value}
      onChange={handleChange}
      placeholder="Select labels"
      inputValue={search}
      onInputChange={setSearch}
      noOptionsMessage={search ? 'Nothing found' : 'Type to see suggestions'}
    />
  );
};
