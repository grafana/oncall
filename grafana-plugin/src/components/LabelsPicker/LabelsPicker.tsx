import React, { FC, useMemo, useState } from 'react';

import { SelectableValue } from '@grafana/data';
import { AsyncSelect, Button, Field, HorizontalGroup, IconButton, VerticalGroup } from '@grafana/ui';

import EditModal from './EditModal';

interface KeyValue {
  key: SelectableValue<string>;
  value: SelectableValue<string>;
}

interface LabelsPickerProps {
  value: KeyValue[];
  loadKeys: (search: string) => Promise<any>;
  loadValuesForKey: (key: SelectableValue['value'], search: string) => Promise<any>;
  createKey: (name: string) => Promise<any>;
  createValue: (keyId: SelectableValue['value'], name: string) => Promise<any>;
  onKeyNameChange: (keyId: SelectableValue['value'], name: string) => Promise<any>;
  onKeyValueNameChange: (
    keyId: SelectableValue['value'],
    valueId: SelectableValue['value'],
    name: string
  ) => Promise<any>;
  labelField: string;
  valueField: string;
  onChange: (value) => void;
  errors: Record<string, any>;
}

const LabelsPicker: FC<LabelsPickerProps> = (props) => {
  const {
    value: propsValue,
    loadKeys,
    loadValuesForKey,
    createKey,
    createValue,
    onKeyNameChange,
    onKeyValueNameChange,
    labelField,
    valueField,
    onChange,
    errors,
  } = props;

  const [indexToShowKeyEditModal, setIndexToShowKeyEditModal] = useState<number>(undefined);
  const [indexToShowValueEditModal, setIndexToShowValueEditModal] = useState<number>(undefined);

  const value = useMemo(() => {
    return propsValue.map((v) => {
      return {
        key: { label: v.key[labelField], value: v.key[valueField] },
        value: { label: v.value[labelField], value: v.value[valueField] },
      };
    });
  }, [propsValue]);

  const loadKeysHandler = (search) => {
    return loadKeys(search).then((keys) => keys.map((key) => ({ label: key[labelField], value: key[valueField] })));
  };

  const loadValuesHandler = (key: SelectableValue['value'], search) => {
    return loadValuesForKey(key, search).then((values) => {
      return values.map((value) => ({ label: value[labelField], value: value[valueField] }));
    });
  };

  const onKeyChange = (index, value) => {
    const newPropsValue = [...propsValue];
    newPropsValue[index] = {
      key: { [labelField]: value.label, [valueField]: value.value },
      value: { [labelField]: undefined, [valueField]: undefined },
    };

    onChange(newPropsValue);
  };

  const changeKeyName = (index, value) => {
    const keyId = propsValue[index].key[valueField];
    onKeyNameChange(keyId, value).then((data) => {
      const newPropsValue = [...propsValue];

      newPropsValue[index] = {
        ...newPropsValue[index],
        key: { [labelField]: data[labelField], [valueField]: data[valueField] },
      };

      onChange(newPropsValue);
    });
  };

  const changeKeyValueName = (index, value) => {
    const keyId = propsValue[index].key[valueField];
    const valueId = propsValue[index].value[valueField];
    onKeyValueNameChange(keyId, valueId, value).then((data) => {
      const newPropsValue = [...propsValue];

      newPropsValue[index] = {
        ...newPropsValue[index],
        value: { [labelField]: data[labelField], [valueField]: data[valueField] },
      };

      onChange(newPropsValue);
    });
  };

  const onValueChange = (index, value) => {
    const newPropsValue = [...propsValue];
    newPropsValue[index] = { ...newPropsValue[index], value: { [labelField]: value.label, [valueField]: value.value } };

    onChange(newPropsValue);
  };

  const onKeyAdd = (index, name) => {
    createKey(name).then((key) => {
      const newPropsValue = [...propsValue];

      newPropsValue[index] = {
        key: { [labelField]: key[labelField], [valueField]: key[valueField] },
        value: { [labelField]: undefined, [valueField]: undefined },
      };

      onChange(newPropsValue);
    });
  };

  const onValueAdd = (index, value) => {
    const keyId = propsValue[index].key[valueField];
    createValue(keyId, value).then((data) => {
      const newPropsValue = [...propsValue];

      newPropsValue[index] = {
        ...newPropsValue[index],
        value: { [labelField]: data[labelField], [valueField]: data[valueField] },
      };

      onChange(newPropsValue);
    });
  };

  const handleLabelRemove = (index: number) => {
    // @ts-ignore
    onChange(propsValue.toSpliced(index, 1));
  };

  const handleLabelAdd = () => {
    onChange([
      ...propsValue,
      {
        key: { [labelField]: undefined, [valueField]: undefined },
        value: { [labelField]: undefined, [valueField]: undefined },
      },
    ]);
  };

  return (
    <>
      <div className="labels-list">
        <VerticalGroup>
          {value.map((keyValue, index) => (
            <HorizontalGroup key={index} spacing="xs" align="flex-start">
              <Field className="label-field" invalid={errors[index]?.key} error={errors[index]?.key?.[valueField]}>
                <AsyncSelect
                  width={256 / 8}
                  value={keyValue.key.value ? keyValue.key : undefined} // to show placeholder correctly
                  loadOptions={loadKeysHandler}
                  defaultOptions
                  onChange={(value) => onKeyChange(index, value)}
                  placeholder="Select key"
                  autoFocus
                  allowCustomValue
                  onCreateOption={(value) => onKeyAdd(index, value.trim())}
                  cacheOptions={false}
                  // @ts-ignore actually it works
                  isOptionDisabled={(item) => {
                    return index === value.length - 1 && value.some((v) => v.key.value === item.value);
                  }}
                  filterOption={(item) => {
                    return index !== value.length - 1 || !value.some((v) => v.key.value === item.value);
                  }}
                  formatOptionLabel={(item) => {
                    return (
                      <HorizontalGroup>
                        {item.label}
                        {keyValue.key.value === item.value && (
                          <IconButton
                            className="pair-edit"
                            size="xs"
                            name="pen"
                            aria-label="Edit Key"
                            onClick={(event: React.SyntheticEvent) => {
                              event.stopPropagation();

                              setIndexToShowKeyEditModal(index);
                            }}
                          />
                        )}
                      </HorizontalGroup>
                    );
                  }}
                />
              </Field>

              <Field className="label-field" invalid={errors[index]?.value} error={errors[index]?.key?.[valueField]}>
                <AsyncSelect
                  key={keyValue.key.value}
                  width={256 / 8}
                  disabled={!keyValue.key.value}
                  value={keyValue.value.value ? keyValue.value : undefined} // to show placeholder correctly
                  loadOptions={(search) => loadValuesHandler(keyValue.key.value, search)}
                  defaultOptions
                  onChange={(value) => onValueChange(index, value)}
                  allowCustomValue
                  onCreateOption={(value) => onValueAdd(index, value.trim())}
                  placeholder={keyValue.key.value ? 'Select value' : 'Select key first'}
                  autoFocus
                  cacheOptions={false}
                  formatOptionLabel={(item) => (
                    <HorizontalGroup>
                      {item.label}
                      {keyValue.value.value === item.value && (
                        <IconButton
                          className="pair-edit"
                          size="xs"
                          name="pen"
                          aria-label="Edit Key"
                          onClick={(event: React.SyntheticEvent) => {
                            event.stopPropagation();

                            setIndexToShowValueEditModal(index);
                          }}
                        />
                      )}
                    </HorizontalGroup>
                  )}
                />
              </Field>

              <Field className="label-field">
                <Button
                  disabled={false}
                  tooltip="Remove label"
                  variant="secondary"
                  icon="times"
                  onClick={() => handleLabelRemove(index)}
                />
              </Field>
              {index === value.length - 1 && (
                <Field className="label-field">
                  <Button
                    disabled={false}
                    tooltip="Add label"
                    variant="secondary"
                    icon="plus"
                    onClick={handleLabelAdd}
                  />
                </Field>
              )}
            </HorizontalGroup>
          ))}

          {!value.length && (
            <Button disabled={false} tooltip="Add label" variant="primary" icon="plus" onClick={handleLabelAdd}>
              Label
            </Button>
          )}
        </VerticalGroup>
      </div>
      {indexToShowKeyEditModal !== undefined && (
        <EditModal
          isKeyEdit
          keyString={propsValue[indexToShowKeyEditModal].key[labelField]}
          onDismiss={() => setIndexToShowKeyEditModal(undefined)}
          onKeyUpdate={(value) => changeKeyName(indexToShowKeyEditModal, value)}
          isInUse={false}
        />
      )}
      {indexToShowValueEditModal !== undefined && (
        <EditModal
          isKeyEdit={false}
          keyString={propsValue[indexToShowValueEditModal].key[labelField]}
          valueString={propsValue[indexToShowValueEditModal].value[labelField]}
          onDismiss={() => setIndexToShowValueEditModal(undefined)}
          onValueUpdate={(value) => changeKeyValueName(indexToShowValueEditModal, value)}
          isInUse={false}
        />
      )}
    </>
  );
};

export default LabelsPicker;
