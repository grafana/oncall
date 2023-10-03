// @ts-ignore
import { Button, HorizontalGroup, IconButton, Select, VerticalGroup } from '@grafana/ui';
import React, { FC, useState } from 'react';
import { ItemGroup, ItemRepresentation, ItemSelected } from 'components/LatestLabelsPicker/core/types';

import 'components/LatestLabelsPicker/components/ServiceLabels/ServiceLabels.css';
import EditModal, { BaseEditModal } from 'components/LatestLabelsPicker/components/EditModal/EditModal';

interface KeyValueProps {
  selectedOptions: ItemSelected[];

  onLoadKeys: () => Promise<ItemRepresentation[]>;
  onLoadValuesForKey: (key: string) => Promise<ItemRepresentation[]>;
  onCreateKey: (key: string) => Promise<{ key: ItemRepresentation; values: ItemRepresentation[] }>;
  onUpdateKey: (keyId: string, keyName: string) => Promise<ItemRepresentation>;
  onCreateValue: (keyId: string, value: string) => Promise<ItemRepresentation>;
  onUpdateValue: (keyId: string, valueId: string, value: string) => Promise<ItemRepresentation>;
  onRowItemRemoval: (pair: ItemSelected, index: number) => any;
  onDataUpdate: (result: ItemSelected[]) => any;
}

const FieldId = 'id';
const FieldName = 'repr';

const ServiceLabels: FC<KeyValueProps> = ({
  selectedOptions: selectedOptionsProps,

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
  const [selectedOptions, setSelectedOptions] = useState<ItemSelected[]>(selectedOptionsProps);
  const [allOptions, setAllOptions] = useState<ItemGroup[]>(getInitialAllOptions());

  const [modalInfo, setModalInfo] = useState<BaseEditModal>(initModalInfo());

  const getAllKeys = () =>
    allOptions.map((option) => ({
      label: option.key[FieldName],
      value: option.key[FieldName],
    }));

  const getAllValues = (option: ItemSelected) =>
    allOptions
      .find((opt) => opt.key[FieldName] === option.key[FieldName])
      ?.values.map((val) => ({
        label: val[FieldName],
        value: val[FieldName],
      }));

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
            <div className="pair-selector">
              <Select
                width={256 / 8}
                value={option.key[FieldName]}
                options={getAllKeys()}
                onChange={(value) => onKeyChange(value.value, index)}
                placeholder="Select key"
                autoFocus
                allowCustomValue
                onCreateOption={(key) => onKeyAdd(key.trim(), index)}
              />
              {option.key[FieldName] && (
                <IconButton
                  className="pair-edit"
                  size="xs"
                  name="pen"
                  aria-label="Edit Key"
                  onClick={(event: React.SyntheticEvent) => onKeyEdit(event, option, index)}
                />
              )}
            </div>

            <div className="pair-selector">
              <Select
                width={256 / 8}
                disabled={!option.key[FieldName] || loadingKeys.indexOf(option.key[FieldId]) !== -1}
                value={option.value[FieldName]}
                options={getAllValues(option)}
                onChange={(value) => onValueChange(option.key[FieldName], value.value, index)}
                allowCustomValue
                onCreateOption={(value) => onValueAdd(option.key[FieldId], value.trim(), index)}
                placeholder={option.key ? 'Select value' : 'Select key first'}
                autoFocus
              />
              {option.value?.[FieldName] && (
                <IconButton
                  className="pair-edit"
                  name="pen"
                  size="xs"
                  aria-label="Edit Value"
                  onClick={(event: React.SyntheticEvent) => onValueEdit(event, option, index)}
                />
              )}
            </div>

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

  function getInitialAllOptions() {
    let allOpt: ItemGroup[] = [];
    selectedOptions.forEach((option) =>
      allOpt.push({
        key: option.key,
        values: [option.value],
      })
    );

    return allOpt;
  }

  function updateSelectedOptions(selectedOptions: ItemSelected[]) {
    setSelectedOptions(selectedOptions);
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
    await onLoadKeys().then((res) => {
      setAllOptions(
        res.map((responseKey) => ({
          key: responseKey,
          values: [],
        }))
      );

      updateSelectedOptions([
        ...selectedOptions,
        {
          key: { [FieldId]: undefined, [FieldName]: undefined },
          value: { [FieldId]: undefined, [FieldName]: undefined },
        },
      ]);
    });
  }

  async function onEditKeyUpdate(keyId: string, keyName: string, rowIndex: number) {
    onUpdateKey(keyId, keyName).then((keyResponse) => {
      const newSelectedOptions = [...selectedOptions];
      newSelectedOptions[rowIndex] = {
        key: keyResponse,
        value: newSelectedOptions[rowIndex].value,
      };

      appendLoadingKey(keyId);

      onLoadValuesForKey(keyId)
        .then((valuesResponse) => {
          const newAllOptions = [...allOptions];
          newAllOptions.push({
            key: keyResponse,
            values: valuesResponse,
          });

          setAllOptions(newAllOptions);
          updateSelectedOptions(newSelectedOptions);
          setModalInfo(initModalInfo());
        })
        .finally(() => removeLoadingKey(keyId));
    });
  }

  async function onEditValueUpdate(keyId: string, valueId: string, value: string, rowIndex: number) {
    onUpdateValue(keyId, valueId, value).then((valueResponse) => {
      const newSelectedOptions = [...selectedOptions];
      newSelectedOptions[rowIndex] = {
        key: newSelectedOptions[rowIndex].key,
        value: valueResponse,
      };

      appendLoadingKey(keyId);

      onLoadValuesForKey(keyId)
        .then((valuesForKey) => {
          const newAllOptions = [...allOptions];
          const found = newAllOptions.find((o) => o.key[FieldId] === keyId);
          found.values = valuesForKey;

          updateSelectedOptions(newSelectedOptions);
          setAllOptions(newAllOptions);
          setModalInfo(initModalInfo());
        })
        .finally(() => removeLoadingKey(keyId));
    });
  }

  async function onKeyChange(key: string, rowIndex: number) {
    const found = allOptions.find((o) => o.key[FieldName] === key);

    const newSelectedOptions = selectedOptions.map((opt, index) =>
      index === rowIndex
        ? {
            key: found.key,
            value: { [FieldId]: null, [FieldName]: null },
          }
        : opt
    );

    updateSelectedOptions(newSelectedOptions);
    appendLoadingKey(found.key[FieldId]);

    await onLoadValuesForKey(found.key[FieldId])
      .then((valuesResponse) => {
        found.values = valuesResponse;
        const newAllOptions = allOptions.map((opt) => (opt.key[FieldName] === key ? found : opt));
        setAllOptions(newAllOptions);
      })
      .finally(() => removeLoadingKey(found.key[FieldId]));
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
      const newAllOptions = [...allOptions, { key: newKey.key, values: [] }];

      updateSelectedOptions(newSelectedOptions);
      setAllOptions(newAllOptions);
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

      appendLoadingKey(keyId);

      onLoadValuesForKey(keyId).then((valuesResponse) => {
        const newAllOptions = allOptions.map((opt) =>
          opt.key[FieldId] === keyId
            ? {
                key: opt.key,
                values: valuesResponse,
              }
            : opt
        );

        updateSelectedOptions(newSelectedOptions);
        setAllOptions(newAllOptions);
      }).finally(() => removeLoadingKey(keyId));
    });
  }

  function onValueChange(key: string, value: string, rowIndex: number) {
    // check for duplicate
    if (selectedOptions.find((option) => option.key[FieldName] === key && option.value[FieldName] === value)) return;

    const option = allOptions.find((k) => k.key[FieldName] === key);
    const foundValue = option.values.find((v) => v[FieldName] === value);
    const newSelectedOptions = selectedOptions.map((opt, index) =>
      index === rowIndex
        ? {
            key: opt.key,
            value: foundValue,
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
      isInUse: false,
      rowIndex: -1,
    };
  }

  function onKeyEdit(e: React.SyntheticEvent, option: ItemSelected, rowIndex: number) {
    e.stopPropagation();

    setModalInfo({
      isKeyEdit: true,
      isOpen: true,
      option,
      isInUse: !!allOptions[option.key[FieldName]],
      rowIndex,
    });
  }

  function onValueEdit(event: React.SyntheticEvent, option: ItemSelected, rowIndex: number) {
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
