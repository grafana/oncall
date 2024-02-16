// @ts-nocheck

import React, { FC, useState } from 'react';

import { css } from '@emotion/css';
import { AsyncSelect, Button, Field, HorizontalGroup, IconButton, VerticalGroup, useStyles2 } from '@grafana/ui';
import { KEY_ERROR_MESSAGE, VALUE_ERROR_MESSAGE } from 'core/consts';
import { ItemSelected, LabelInputType, ServiceLabelValidator } from 'core/types';
import { omit } from 'lodash-es';

import { EditModal, BaseEditModal } from 'components/EditModal/EditModal';

export interface ServiceLabelsProps {
  loadById?: boolean;
  inputWidth?: number;
  isEditable?: boolean;
  value: ItemSelected[];

  valueField?: string;
  labelField?: string;

  errors?: Record<string, any>;

  onLoadKeys: (search: string) => Promise<any[]>;
  onLoadValuesForKey: (key: string, search: string) => Promise<any[]>;
  onCreateKey: (key: string) => Promise<{ key: any; values: any[] }>;
  onUpdateKey: (keyId: string, keyName: string) => Promise<any>;
  onCreateValue: (keyId: string, value: string) => Promise<any>;
  onUpdateValue: (keyId: string, valueId: string, value: string) => Promise<any>;
  onDataUpdate: (result: ItemSelected[]) => any;
  onUpdateError: (result: any) => void;

  getIsKeyEditable?: (key: ItemSelected['key']) => boolean;
  getIsValueEditable?: (value: ItemSelected['value']) => boolean;

  openErrorNotification?(message: string): any;
  onRowItemRemoval?: (pair: ItemSelected, index: number) => any;
  onDuplicateKeySelect?: (key) => any;

  // allow consumer to plug-in custom field validator
  keyValidator?: (key: string) => ServiceLabelValidator;
  valueValidator?: (value: string) => ServiceLabelValidator;

  isAddingDisabled?: boolean;
  renderValue?: (
    item: ItemSelected,
    index: number,
    renderValueDefault: (item: ItemSelected, index: number) => React.ReactNode
  ) => React.ReactNode;
}

const KEY_REGEX_RULE = /^([A-Za-z][A-Za-z0-9_]*)?[A-Za-z]$/;
const VALUE_REGEX_RULE = /^(([A-Za-z0-9][-A-Za-z0-9_.]*)?[A-Za-z0-9])?$/;
const DUPLICATE_ERROR = 'Duplicate keys are not allowed.';

export const ServiceLabels: FC<ServiceLabelsProps> = ({
  loadById = true,
  inputWidth = 276,
  isEditable = true,
  value: selectedOptions,
  errors = {},

  valueField: FieldId = 'id',
  labelField: FieldName = 'name',

  onLoadKeys,
  onLoadValuesForKey,
  onCreateKey,
  onUpdateKey,
  onCreateValue,
  onUpdateValue,
  onRowItemRemoval,
  onDataUpdate,
  onUpdateError,
  onDuplicateKeySelect,
  isAddingDisabled = false,
  renderValue,
  keyValidator,
  valueValidator,

  getIsKeyEditable = () => true,
  getIsValueEditable = () => true,
}) => {
  const styles = useStyles2(() => getStyles());

  const [keyErrors, setKeyErrors] = useState({});
  const [valueErrors, setValueErrors] = useState({});

  const [loadingKeys, setLoadingKeys] = useState<string[]>([]);
  const [duplicatedKey, setDuplicatedKey] = useState<{
    key: string;
    index: number;
  }>(undefined);
  const [modalInfo, setModalInfo] = useState<BaseEditModal>(initModalInfo());

  const renderValueDefault = (option: ItemSelected, index: number) => {
    const isValueDisabled = !option.key[FieldName] || loadingKeys.indexOf(option.key[getLookoutMethod()]) !== -1;

    return (
      <>
        <AsyncSelect
          key={`${option.key[FieldName]}-${option.value[FieldName]}`}
          width={inputWidth / 8}
          disabled={isValueDisabled}
          value={
            option.value[FieldId]
              ? {
                  value: option.value[FieldId],
                  label: option.value[FieldName],
                }
              : undefined
          }
          defaultOptions
          loadOptions={loadOptionsValues.bind(undefined, option)}
          onChange={(value) => {
            setValueErrors({
              ...valueErrors,
              [index]: undefined,
            });
            onValueChange(option.key[FieldName], value, index);
          }}
          allowCustomValue
          cacheOptions={false}
          onCreateOption={(value) => onValueCreateOption(value, option, index)}
          placeholder={option.key ? 'Select value' : 'Select key first'}
          noOptionsMessage="No values found"
          menuShouldPortal
        />

        {option.value?.[FieldName] && isEditable && getIsValueEditable(option.value) && (
          <IconButton
            className={styles.edit}
            name="pen"
            size="xs"
            aria-label="Edit Value"
            tooltip="Edit Value"
            onClick={(event: React.SyntheticEvent) => onOpenValueEditModal(event, option, index)}
          />
        )}
      </>
    );
  };

  return (
    <div>
      {modalInfo.isOpen && (
        <EditModal
          {...modalInfo}
          onUpdateError={onUpdateError}
          valueField={FieldId}
          labelField={FieldName}
          onDismiss={() => setModalInfo(initModalInfo())}
          onKeyUpdate={onEditKeyUpdate}
          onValueUpdate={onEditValueUpdate}
          validateUserInput={validateUserInput}
        />
      )}

      <VerticalGroup>
        {selectedOptions.map((option, index) => (
          <HorizontalGroup key={index} spacing="xs" align="flex-start">
            <div className={styles.wrapper}>
              <Field
                invalid={!!keyErrors[index] || errors[index]?.key || duplicatedKey?.index === index}
                error={
                  keyErrors[index] ||
                  errors[index]?.key?.[FieldId] ||
                  (duplicatedKey?.index === index && DUPLICATE_ERROR)
                }
              >
                <div className={styles.selector}>
                  <AsyncSelect
                    // the key uniqueness guarantess that AsyncSelector is always updated and we don't run into any bug
                    key={`${option.key[FieldName]}${
                      option.key[FieldName] === undefined ? Math.floor(Math.random() * 1000) : ''
                    }`}
                    width={inputWidth / 8}
                    value={
                      option.key[FieldId]
                        ? {
                            value: option.key[FieldId],
                            label: option.key[FieldName],
                          }
                        : undefined
                    }
                    defaultOptions
                    loadOptions={loadOptionsKeys}
                    onChange={(value) => {
                      onKeyChange(value, index);
                      setKeyErrors({
                        ...keyErrors,
                        [index]: undefined,
                      });
                    }}
                    placeholder="Select key"
                    allowCustomValue
                    cacheOptions={false}
                    onCreateOption={(key: string) => onKeyCreateOption(key, index)}
                    noOptionsMessage="No labels found"
                    menuShouldPortal
                  />
                  {option.key[FieldName] && isEditable && getIsKeyEditable(option.key) && (
                    <IconButton
                      className={styles.edit}
                      size="xs"
                      name="pen"
                      aria-label="Edit Key"
                      tooltip="Edit Key"
                      onClick={(event: React.SyntheticEvent) => onOpenKeyEditModal(event, option, index)}
                    />
                  )}
                </div>
              </Field>
            </div>

            <div className={styles.wrapper}>
              <Field
                invalid={!!valueErrors[index] || errors[index]?.value}
                error={valueErrors[index] || errors[index]?.value?.[FieldName]}
              >
                <div className={styles.selector}>
                  {renderValue ? renderValue(option, index, renderValueDefault) : renderValueDefault(option, index)}
                </div>
              </Field>
            </div>

            <div className={[styles.actions, styles.wrapper].join(' ')}>
              <Field>
                <HorizontalGroup spacing="md">
                  <Button
                    disabled={false}
                    tooltip="Remove label"
                    variant="secondary"
                    icon="times"
                    onClick={() => onRowRemoval(option, index)}
                  />
                </HorizontalGroup>
              </Field>
            </div>
          </HorizontalGroup>
        ))}

        {!isAddingDisabled && selectedOptions.length > 0 ? (
          <div className={styles.addRow}>
            <Button disabled={isAddDisabled()} variant="secondary" icon="plus" onClick={handleLabelAdd}>
              Add
            </Button>
          </div>
        ) : (
          !isAddingDisabled && (
            <Button disabled={false} variant="primary" icon="plus" onClick={handleLabelAdd}>
              Add Labels
            </Button>
          )
        )}
      </VerticalGroup>
    </div>
  );

  function onKeyCreateOption(key: string, index: number) {
    const { isValid, errorMessage } = validateUserInput(key, LabelInputType.key);

    if (isValid) {
      delete keyErrors[index];
      return onKeyAdd(key.trim(), index);
    }

    onDataUpdate(
      selectedOptions.map((o, i) =>
        index === i
          ? {
              // set key to undefined instead of preserving the old one
              key: {
                [FieldId]: undefined,
                [FieldName]: undefined,
              },
              // also clear value
              value: {
                [FieldId]: undefined,
                [FieldName]: undefined,
              },
            }
          : o
      )
    );

    setKeyErrors({
      ...keyErrors,
      [index]: errorMessage || KEY_ERROR_MESSAGE,
    });
  }

  function onValueCreateOption(value: string, option: ItemSelected, index: number) {
    const { isValid, errorMessage } = validateUserInput(value, LabelInputType.value);

    if (isValid) {
      delete valueErrors[index];
      return onValueAdd(option.key[getLookoutMethod()], value.trim(), index);
    }

    onDataUpdate(
      selectedOptions.map((o, i) =>
        index === i
          ? {
              key: o.key,
              // set value to undefined instead of preserving the old one
              value: { [FieldId]: undefined, [FieldName]: undefined },
            }
          : o
      )
    );

    setValueErrors({
      ...valueErrors,
      [index]: errorMessage || VALUE_ERROR_MESSAGE,
    });
  }

  function validateUserInput(fieldValue: string, type: LabelInputType) {
    if (type === LabelInputType.key && keyValidator) {
      return keyValidator(fieldValue);
    } else if (type === LabelInputType.value && valueValidator) {
      return valueValidator(fieldValue);
    }

    return {
      isValid:
        (type === LabelInputType.key ? KEY_REGEX_RULE : VALUE_REGEX_RULE).test(fieldValue) &&
        fieldValue.trim().length > 0 &&
        fieldValue.length <= 61,
    } as ServiceLabelValidator;
  }

  function getStyles() {
    return {
      heading: css`
        font-size: 18px;
      `,
      selector: css`
        display: flex;
        position: relative;
        margin-bottom: -8px;

        &:hover > button {
          visibility: visible;
        }
      `,
      edit: css`
        position: absolute !important;
        z-index: 1000 !important;
        top: 50%;
        right: 26px;
        transform: translateY(-50%);
        visibility: hidden;
        background-color: transparent;
        cursor: pointer;

        &:hover::before {
          background-color: unset !important;
        }
      `,
      actions: css`
        margin-left: 8px;
      `,
      wrapper: css`
        & > div {
          margin-bottom: 0px;
        }
      `,
      addRow: css`
        padding-top: 16px;
      `,
    };
  }

  function remapToFieldNameAndFieldId(arr) {
    return arr.map((item) => {
      const newItem = {
        label: item[FieldName],
        value: item[FieldId],
        ...omit(item, [FieldName, FieldId]),
      };

      if (item.options) {
        (newItem as any).options = remapToFieldNameAndFieldId(item.options);
      }
      return newItem;
    });
  }

  async function loadOptionsKeys(search = '') {
    return onLoadKeys(search).then((keys) => {
      return remapToFieldNameAndFieldId(keys);
    });
  }

  async function loadOptionsValues(option: ItemSelected, search = '') {
    return onLoadValuesForKey(option.key[getLookoutMethod()], search).then((values) => {
      return remapToFieldNameAndFieldId(values);
    });
  }

  function getLookoutMethod() {
    return loadById ? FieldId : FieldName;
  }

  function updateSelectedOptions(selectedOptions: ItemSelected[]) {
    onDataUpdate(selectedOptions);
  }

  function isAddDisabled() {
    if (!selectedOptions.length) {
      return false;
    }
    const lastItem = selectedOptions[selectedOptions.length - 1];
    return !lastItem.key[FieldName] || !lastItem.value[FieldName];
  }

  function appendLoadingKey(keyId: string) {
    setLoadingKeys([...loadingKeys, keyId]);
  }

  function removeLoadingKey(keyId: string) {
    setLoadingKeys(loadingKeys.filter((n) => n !== keyId));
  }

  async function handleLabelAdd() {
    await onLoadKeys('').then(() => {
      updateSelectedOptions([
        ...selectedOptions,
        {
          key: { [FieldId]: undefined, [FieldName]: undefined },
          value: { [FieldId]: undefined, [FieldName]: undefined },
        },
      ]);
    });
  }

  async function onEditKeyUpdate(keyId: string, keyName: string, rowIndex: number): Promise<void> {
    try {
      const keyResponse = await onUpdateKey(keyId, keyName);
      const newSelectedOptions = [...selectedOptions];
      newSelectedOptions[rowIndex] = {
        key: keyResponse,
        value: newSelectedOptions[rowIndex].value,
      };

      appendLoadingKey(keyId);

      updateSelectedOptions(newSelectedOptions);
      setModalInfo(initModalInfo());
    } finally {
      removeLoadingKey(keyId);
    }
  }

  async function onEditValueUpdate(keyId: string, valueId: string, value: string, rowIndex: number): Promise<void> {
    try {
      const valueResponse = await onUpdateValue(keyId, valueId, value);
      const newSelectedOptions = [...selectedOptions];
      newSelectedOptions[rowIndex] = {
        key: newSelectedOptions[rowIndex].key,
        value: valueResponse,
      };

      appendLoadingKey(keyId);

      updateSelectedOptions(newSelectedOptions);
      setModalInfo(initModalInfo());
    } finally {
      removeLoadingKey(keyId);
    }
  }

  async function onKeyChange(option: any, rowIndex: number) {
    const duplicate = selectedOptions.find((o) => o.key[FieldName] === option.label);

    if (duplicate) {
      setDuplicatedKey({ key: duplicate.key[FieldName], index: rowIndex });

      onDuplicateKeySelect?.(duplicate);
      return;
    }

    if (duplicatedKey && rowIndex === duplicatedKey.index) {
      setDuplicatedKey(undefined); // clear error message
    }

    const newSelectedOptions = selectedOptions.map((opt, index) =>
      index === rowIndex
        ? {
            key: { [FieldId]: option.value, [FieldName]: option.label, ...omit(option, ['label', 'value']) },
            value:
              opt.value[FieldId] === null
                ? // if it's null we preserve the value
                  {
                    [FieldId]: opt.value[FieldId],
                    [FieldName]: opt.value[FieldName],
                    ...omit(opt, ['label', 'value']),
                  }
                : // otherwise we reset it because it should be empty afterwards you change the key
                  { [FieldId]: undefined, [FieldName]: undefined },
          }
        : opt
    );

    updateSelectedOptions(newSelectedOptions);
  }

  async function onKeyAdd(key: string, rowIndex: number) {
    if (!key) {
      return;
    }

    onCreateKey(key).then((res) => {
      const newKey = {
        key: { [FieldId]: res[FieldId], [FieldName]: res[FieldName] },
        value: selectedOptions[rowIndex].value,
      };

      const newSelectedOptions = [...selectedOptions];
      newSelectedOptions[rowIndex] = newKey;

      updateSelectedOptions(newSelectedOptions);
    });
  }

  async function onValueAdd(keyId: string, value: string, rowIndex: number) {
    if (!value) {
      return;
    }

    onCreateValue(keyId, value).then((valueResponse) => {
      const newSelectedOptions = [...selectedOptions];
      newSelectedOptions[rowIndex] = {
        key: newSelectedOptions[rowIndex].key,
        value: valueResponse,
      };

      updateSelectedOptions(newSelectedOptions);
    });
  }

  function onValueChange(key: string, option: any, rowIndex: number) {
    // prevent duplicates
    if (selectedOptions.find((opt) => opt.key[FieldName] === key && opt.value[FieldName] === option.label)) {
      return;
    }

    const newSelectedOptions = selectedOptions.map((opt, index) =>
      index === rowIndex
        ? {
            key: opt.key,
            value: { [FieldId]: option.value, [FieldName]: option.label, ...omit(option, 'label', 'value') },
          }
        : opt
    );

    updateSelectedOptions(newSelectedOptions);
  }

  function onRowRemoval(option: ItemSelected, rowIndex: number) {
    const newSelectedOptions = [...selectedOptions];
    newSelectedOptions.splice(rowIndex, 1);
    updateSelectedOptions(newSelectedOptions);
    setDuplicatedKey(undefined);

    clearInvalidRowError(rowIndex);

    if (onRowItemRemoval) {
      onRowItemRemoval(option, rowIndex);
    }
  }

  function clearInvalidRowError(rowIndex: number) {
    setValueErrors({
      ...valueErrors,
      [rowIndex]: undefined,
    });

    setKeyErrors({
      ...keyErrors,
      [rowIndex]: undefined,
    });
  }

  function initModalInfo(): BaseEditModal {
    return {
      isKeyEdit: false,
      isOpen: false,
      option: undefined,
      rowIndex: -1,
    };
  }

  function onOpenKeyEditModal(e: React.SyntheticEvent, option: ItemSelected, rowIndex: number) {
    e.stopPropagation();

    setModalInfo({
      isKeyEdit: true,
      isOpen: true,
      option,
      rowIndex,
    });
  }

  function onOpenValueEditModal(event: React.SyntheticEvent, option: ItemSelected, rowIndex: number) {
    event.stopPropagation();

    setModalInfo({
      isKeyEdit: false,
      isOpen: true,
      option,
      rowIndex,
    });
  }
};
