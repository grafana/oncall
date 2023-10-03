import { AsyncSelect, Button, Field, HorizontalGroup, IconButton, VerticalGroup } from '@grafana/ui';
import React, { FC, useState } from 'react';
import { ItemSelected } from 'components/LatestLabelsPicker/core/types';

import 'components/LatestLabelsPicker/components/ServiceLabels/ServiceLabels.css';
import EditModal, { BaseEditModal } from 'components/LatestLabelsPicker/components/EditModal/EditModal';

interface KeyValueProps {
  inputWidth?: number;
  value: ItemSelected[];
  loadById: boolean;

  valueField?: string;
  labelField?: string;

  errors: Record<string, any>;

  onLoadKeys: (search: string) => Promise<any[]>;
  onLoadValuesForKey: (key: string, search: string) => Promise<any[]>;
  onCreateKey: (key: string) => Promise<{ key: any; values: any[] }>;
  onUpdateKey: (keyId: string, keyName: string) => Promise<any>;
  onCreateValue: (keyId: string, value: string) => Promise<any>;
  onUpdateValue: (keyId: string, valueId: string, value: string) => Promise<any>;
  onRowItemRemoval?: (pair: ItemSelected, index: number) => any;
  onDataUpdate: (result: ItemSelected[]) => any;
}

const ServiceLabels: FC<KeyValueProps> = ({
  loadById,
  inputWidth = 256,
  value: selectedOptions,
  errors,

  valueField: FieldId = 'id',
  labelField: FieldName = 'repr',

  onLoadKeys,
  onLoadValuesForKey,
  onCreateKey,
  onUpdateKey,
  onCreateValue,
  onUpdateValue,
  onRowItemRemoval,
  onDataUpdate,
}) => {
  const [loadingKeys, setLoadingKeys] = useState<string[]>([]);
  const [modalInfo, setModalInfo] = useState<BaseEditModal>(initModalInfo());

  return (
    <div>
      {modalInfo.isOpen && (
        <EditModal
          {...modalInfo}
          onDismiss={() => setModalInfo(initModalInfo())}
          onKeyUpdate={onEditKeyUpdate}
          onValueUpdate={onEditValueUpdate}
        />
      )}

      <VerticalGroup>
        {selectedOptions.map((option, index) => (
          <HorizontalGroup key={index} spacing="xs">
            <Field invalid={errors[index]?.key} error={errors[index]?.key?.[FieldId]}>
              <div className="pair-selector">
                <AsyncSelect
                  width={inputWidth / 8}
                  value={option.key[FieldId] ? { value: option.key[FieldId], label: option.key[FieldName] } : undefined}
                  defaultOptions
                  loadOptions={loadOptionsKeys}
                  onChange={(value) => onKeyChange(value, index)}
                  placeholder="Select key"
                  autoFocus
                  allowCustomValue
                  cacheOptions={false}
                  onCreateOption={(key) => onKeyAdd(key.trim(), index)}
                  noOptionsMessage="No labels found"
                  menuShouldPortal
                />
                {option.key[FieldName] && (
                  <IconButton
                    className="pair-edit"
                    size="xs"
                    name="pen"
                    aria-label="Edit Key"
                    onClick={(event: React.SyntheticEvent) => onOpenKeyEditModal(event, option, index)}
                  />
                )}
              </div>
            </Field>

            <Field invalid={errors[index]?.value} error={errors[index]?.key?.[FieldName]}>
              <div className="pair-selector">
                <AsyncSelect
                  key={`${option.key[FieldName]}-${option.value[FieldName]}`}
                  width={inputWidth / 8}
                  disabled={!option.key[FieldName] || loadingKeys.indexOf(option.key[getLookoutMethod()]) !== -1}
                  value={
                    option.value[FieldId] ? { value: option.value[FieldId], label: option.value[FieldName] } : undefined
                  }
                  defaultOptions
                  loadOptions={(search) =>
                    onLoadValuesForKey(option.key[getLookoutMethod()], search).then((values) =>
                      values.map((value) => ({ label: value[FieldName], value: value[FieldId] }))
                    )
                  }
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
                {option.value?.[FieldName] && (
                  <IconButton
                    className="pair-edit"
                    name="pen"
                    size="xs"
                    aria-label="Edit Value"
                    onClick={(event: React.SyntheticEvent) => onOpenValueEditModal(event, option, index)}
                  />
                )}
              </div>
            </Field>

            <Field>
              <HorizontalGroup spacing="md">
                <Button
                  disabled={false}
                  tooltip="Remove label"
                  variant="secondary"
                  icon="times"
                  size="sm"
                  onClick={() => onRowRemoval(option, index)}
                />
                {index === selectedOptions.length - 1 && (
                  <Button
                    disabled={isAddDisabled()}
                    size="sm"
                    tooltip="Add label"
                    variant="secondary"
                    icon="plus"
                    onClick={handleLabelAdd}
                  />
                )}
              </HorizontalGroup>
            </Field>
          </HorizontalGroup>
        ))}

        {!selectedOptions.length && (
          <Button disabled={false} tooltip="Add label" variant="primary" icon="plus" onClick={handleLabelAdd}>
            Add Labels
          </Button>
        )}
      </VerticalGroup>
    </div>
  );

  function loadOptionsKeys(search) {
    return onLoadKeys(search).then((keys) => keys.map((key) => ({ label: key[FieldName], value: key[FieldId] })));
  }

  function getLookoutMethod() {
    return loadById ? FieldId : FieldName;
  }

  function updateSelectedOptions(selectedOptions: ItemSelected[]) {
    onDataUpdate(selectedOptions);
  }

  function isAddDisabled() {
    if (!selectedOptions.length) return false;
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
    await onLoadKeys('').then((_res) => {
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
    // prevent duplicates
    if (selectedOptions.find((o) => o.key[FieldName] === option.value)) return;

    const newSelectedOptions = selectedOptions.map((opt, index) =>
      index === rowIndex
        ? {
            key: { [FieldId]: option.value, [FieldName]: option.label },
            value: { [FieldId]: null, [FieldName]: null },
          }
        : opt
    );

    updateSelectedOptions(newSelectedOptions);
  }

  async function onKeyAdd(key: string, rowIndex: number) {
    if (!key) return;

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
    if (!value) return;

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
    if (selectedOptions.find((opt) => opt.key[FieldName] === key && opt.value[FieldName] === option.value)) return;

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
