import { css } from '@emotion/css';
import { SelectableValue } from '@grafana/data';
import { HorizontalGroup, VerticalGroup, Field, Select, AsyncSelect, Button, useStyles2 } from '@grafana/ui';
import { SplitGroupsResult, splitToGroups } from 'models/label/label.helpers';
import { ApiSchemas } from 'network/oncall-api/api.types';
import React, { useCallback, useEffect, useState } from 'react';
import { useStore } from 'state/useStore';

const FieldId = 'id';
const FieldName = 'name';

enum COMPARISON_TYPE {
  EQUAL = '=',
  NOTEQUAL = '<>',
}

const INITIAL_LABELS_OPTIONS = [
  {
    key: { [FieldId]: undefined, [FieldName]: undefined, prescribed: false },
    comparison: COMPARISON_TYPE.EQUAL,
    value: { [FieldId]: undefined, [FieldName]: undefined, prescribed: false },
  },
];

interface LabelValue {
  key: ApiSchemas['LabelKey'];
  value: ApiSchemas['LabelValue'];
  comparison: COMPARISON_TYPE;
}

interface LabelsQueryBuilderProps {
  values: LabelValue[];
  setValues: (values: LabelValue[]) => void;
}

interface Error {
  [identifier: string]: {
    data: ApiSchemas['LabelKey'] & { error: string };
  };
}

export const LabelsQueryBuilder: React.FC<LabelsQueryBuilderProps> = ({ values, setValues }) => {
  const { labelsStore } = useStore();
  const [, updateState] = useState(undefined);
  const [valueFieldErrors, setValueFieldErrors] = useState<Error>({});
  const forceUpdate = useCallback(() => updateState({}), []);
  const [labelKeys, setLabelKeys] = useState<SplitGroupsResult[]>([]);

  useEffect(() => {
    (async function () {
      const keys = await labelsStore.loadKeys();
      const groups = splitToGroups(keys);
      setLabelKeys(groups);
    })();
  }, []);

  const labelKeysOptions = labelKeys.map(
    (key) =>
      ({
        label: key.name,
        value: key.id,
      } as SelectableValue)
  );

  console.log({ labelKeys: labelKeys, labelKeysOptions });

  const updateValueFieldErrors = (id: string) => {
    const errors = { ...valueFieldErrors };
    if (errors[id]) {
      delete errors[id];
      setValueFieldErrors(errors);
    }
  };

  const onCommonChange = (labelOptionIndex: number, data: Partial<LabelValue>, appendError = false) => {
    const newValues: LabelValue[] = values.map((label, labelIdx) => {
      return labelIdx === labelOptionIndex ? { ...label, ...data } : label;
    });

    const isDuplicate = hasDuplicateLabelEntries(newValues, labelOptionIndex);

    if (!isDuplicate) {
      setValues(newValues);
    } else if (appendError) {
      setValueFieldErrors({
        ...valueFieldErrors,
        [data.value.id]: {
          data: {
            error: 'Duplicates not allowed',
            id: data.value?.id,
            name: data.value?.name,
            prescribed: data.value?.prescribed,
          },
        },
      });
    }

    if (!isDuplicate && appendError) {
      updateValueFieldErrors(data.value.id);
    }

    forceUpdate();
  };

  const onComparisonChange = (option: SelectableValue, labelOptionIndex: number) =>
    onCommonChange(labelOptionIndex, { comparison: option.value });

  const onKeyChange = (option: SelectableValue, labelOptionIndex: number) =>
    // TODO: Figure out prescribed?
    onCommonChange(labelOptionIndex, {
      key: { [FieldId]: option.value, [FieldName]: option.label, prescribed: false },
    });

  const onValueChange = (option: SelectableValue, labelOptionIndex: number) =>
    onCommonChange(
      labelOptionIndex,
      {
        value: {
          [FieldId]: option.value,
          [FieldName]: option.label,
          // TODO: Figure out prescribed?
          prescribed: false,
        },
      },
      true
    );

  const hasDuplicateLabelEntries = (list: LabelValue[], labelOptionIndex: number) => {
    const el = list[labelOptionIndex];
    // compare all other entries with current index
    const duplicateFound = values.find(
      (v, i) =>
        v.key[FieldId] === el.key[FieldId] && // compare by ID
        v.value[FieldId] === el.value[FieldId] && // compare by ID
        v.comparison === el.comparison &&
        i !== labelOptionIndex
    );
    return !!duplicateFound;
  };

  const isAddDisabled = () => {
    const el = values[values.length - 1];
    return el.key[FieldId] === undefined || el.value[FieldId] === undefined || el.comparison === undefined;
  };

  const styles = useStyles2(getStyles);

  return (
    <VerticalGroup>
      {values.map((option, labelOptionIndex) => {
        const valueError = valueFieldErrors[option.value.id];

        return (
          <HorizontalGroup spacing="none" align="flex-start">
            <Field className={cx('field')}>
              <Select
                key={`${option.key[FieldName]}${
                  option.key[FieldName] === undefined ? Math.floor(Math.random() * 1000) : ''
                }`}
                options={labelKeysOptions}
                value={option.key[FieldId]}
                width={250 / 8}
                placeholder="Key"
                onChange={(option: SelectableValue) => onKeyChange(option, labelOptionIndex)}
              />
            </Field>

            <Select
              options={Object.keys(COMPARISON_TYPE).map((k) => ({
                label: COMPARISON_TYPE[k],
                value: COMPARISON_TYPE[k],
              }))}
              value={option.comparison}
              onChange={(option: SelectableValue) => onComparisonChange(option, labelOptionIndex)}
            />

            <Field invalid={!!valueError?.data.error} error={valueError?.data.error} className={cx('field')}>
              <AsyncSelect
                key={`${option.value[FieldName]}${
                  option.value[FieldName] === undefined ? Math.floor(Math.random() * 1000) : ''
                }`}
                width={250 / 8}
                disabled={option.key[FieldName] === undefined}
                value={
                  option.value[FieldName]
                    ? {
                        value: option.value[FieldId],
                        label: option.value[FieldName],
                      }
                    : undefined
                }
                defaultOptions
                loadOptions={async () => {
                  const result = await labelsStore.loadValuesForKey(option.key.id);
                  return result.values.map((v) => ({ label: v.name, value: v.id }));
                }}
                onChange={(option: SelectableValue) => onValueChange(option, labelOptionIndex)}
                cacheOptions={false}
                placeholder={'Value'}
                noOptionsMessage="No values found"
                menuShouldPortal
              />
            </Field>

            <Button
              tooltip="Remove label"
              variant="secondary"
              icon="times"
              onClick={() => {
                if (values.length === 1) {
                  // restore to empty array
                  return setValues(INITIAL_LABELS_OPTIONS);
                }

                setValues(values.slice(labelOptionIndex, 1));
              }}
            />

            <Button
              className={styles.addLabelBtn}
              disabled={isAddDisabled()}
              tooltip="Add"
              variant="secondary"
              icon="plus"
              onClick={() => {
                setValues([...values, ...INITIAL_LABELS_OPTIONS]);
              }}
            ></Button>
          </HorizontalGroup>
        );
      })}
    </VerticalGroup>
  );
};

const getStyles = () => {
  return {
    addLabelBtn: css`
      margin-left: 8px;
    `,
  };
};
