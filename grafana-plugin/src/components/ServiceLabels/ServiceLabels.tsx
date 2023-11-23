import React, { FC, useState } from 'react';

import { css } from '@emotion/css';
import { AsyncSelect, Button, Field, HorizontalGroup, IconButton, VerticalGroup, useStyles2 } from '@grafana/ui';
import { ItemSelected } from 'core/types';

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

  openErrorNotification?(message: string): any;
  onRowItemRemoval?: (pair: ItemSelected, index: number) => any;
  onDuplicateKeySelect?: (key) => any;

  isAddingDisabled?: boolean;
  renderValue?: (
    item: ItemSelected,
    index: number,
    renderValueDefault: (item: ItemSelected, index: number) => React.ReactNode
  ) => React.ReactNode;
}

const DUPLICATE_ERROR = 'Duplicate keys are not allowed.';

const ServiceLabels: FC<ServiceLabelsProps> = ({
  loadById = true,
  inputWidth = 256,
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
}) => {
  const styles = useStyles2(() => getStyles());

  const [loadingKeys, setLoadingKeys] = useState<string[]>([]);
  const [duplicatedKey, setDuplicatedKey] = useState<{
    key: string;
    index: number;
  }>(undefined);
  const [modalInfo, setModalInfo] = useState<BaseEditModal>(initModalInfo());

  const renderValueDefault = (option, index) => {
    return (
      <>
        <AsyncSelect
          key={`${option.key[FieldName]}-${option.value[FieldName]}`}
          width={inputWidth / 8}
          disabled={!option.key[FieldName] || loadingKeys.indexOf(option.key[getLookoutMethod()]) !== -1}
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
            onValueChange(option.key[FieldName], value, index);
          }}
          allowCustomValue
          cacheOptions={false}
          onCreateOption={(value) => onValueAdd(option.key[getLookoutMethod()], value.trim(), index)}
          placeholder={option.key ? 'Select value' : 'Select key first'}
          autoFocus
          noOptionsMessage="No values found"
          menuShouldPortal
        />
        {option.value?.[FieldName] && isEditable && (
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
        />
      )}

      <VerticalGroup>
        {selectedOptions.map((option, index) => (
          <HorizontalGroup key={index} spacing="xs" align="flex-start">
            <div className={styles.wrapper}>
              <Field
                invalid={errors[index]?.key || duplicatedKey?.index === index}
                error={errors[index]?.key?.[FieldId] || (duplicatedKey?.index === index && DUPLICATE_ERROR)}
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
                    onChange={(value) => onKeyChange(value, index)}
                    placeholder="Select key"
                    allowCustomValue
                    cacheOptions={false}
                    onCreateOption={(key) => onKeyAdd(key.trim(), index)}
                    noOptionsMessage="No labels found"
                    menuShouldPortal
                    autoFocus
                  />
                  {option.key[FieldName] && isEditable && (
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
              <Field invalid={errors[index]?.value} error={errors[index]?.value?.[FieldName]}>
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

  async function loadOptionsKeys(search = '') {
    return onLoadKeys(search).then((keys) => keys.map((key) => ({ label: key[FieldName], value: key[FieldId] })));
  }

  async function loadOptionsValues(option: ItemSelected, search = '') {
    return onLoadValuesForKey(option.key[getLookoutMethod()], search).then((values) =>
      values.map((value) => ({
        label: value[FieldName],
        value: value[FieldId],
      }))
    );
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
      if (!selectedOptions[rowIndex].key[FieldName]) {
        // this behavior only happens when no item was previously selected due to the AsyncSelect
        setDuplicatedKey({ key: duplicate.key[FieldName], index: rowIndex });
      }

      onDuplicateKeySelect?.(duplicate);
      return;
    }

    if (duplicatedKey && rowIndex === duplicatedKey.index) {
      setDuplicatedKey(undefined); // clear error message
    }

    const newSelectedOptions = selectedOptions.map((opt, index) =>
      index === rowIndex
        ? {
            key: { [FieldId]: option.value, [FieldName]: option.label },
            value: { [FieldId]: opt.value[FieldId], [FieldName]: opt.value[FieldName] },
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
        value: { [FieldId]: undefined, [FieldName]: undefined },
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
            value: { [FieldId]: option.value, [FieldName]: option.label },
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

    if (onRowItemRemoval) {
      onRowItemRemoval(option, rowIndex);
    }
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

export default ServiceLabels;
