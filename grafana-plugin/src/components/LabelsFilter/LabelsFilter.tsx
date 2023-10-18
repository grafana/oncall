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

const LabelsFilter: FC<LabelsFilterProps> = (props) => {
  const { autoFocus, value: propsValue, labelField: FieldName = 'name', onLoadOptions, onChange } = props;

  const [search, setSearch] = useState('');

  const handleChange = useCallback((value) => {
    onChange(value.map((v) => v.value));
  }, []);

  const handleLoadOptions = (search) => {
    return onLoadOptions(search).then((options) =>
      options.map((v) => ({
        label: `${v.key[FieldName]} : ${v.value[FieldName]}`,
        value: v,
      }))
    );
  };

  const value = useMemo(
    () =>
      propsValue.map((v) => ({
        label: `${v.key[FieldName]} : ${v.value[FieldName]}`,
        value: v,
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

export default LabelsFilter;
