import React, { ChangeEvent, useState } from 'react';
import { ServiceLabels } from '@grafana/labels';
import { Button, Dropdown, Input, Menu, VerticalGroup } from '@grafana/ui';
import { GENERIC_ERROR } from 'utils/consts';
import { openErrorNotification } from 'utils/utils';
import { useStore } from 'state/useStore';
import { splitToGroups } from 'models/label/label.helpers';

interface LabelsQueryDisplay {
  labels: any;
  labelErrors: any;
  onChange: (value: any) => void;
  onShowTemplateEditor: (index: number) => void;
}

const INPUT_WIDTH = 280;

export const LabelsQueryDisplay: React.FC<LabelsQueryDisplay> = ({
  labels,
  labelErrors,
  onChange,
  onShowTemplateEditor,
}) => {
  const { labelsStore } = useStore();

  console.log({ labels });

  // TODO: these 2 can be merged into one
  const handleStaticLabelAdd = () => {
    onChange([
      ...labels,
      {
        key: { id: undefined, name: undefined, prescribed: false },
        value: { id: undefined, name: undefined, prescribed: false },
      },
    ]);
  };

  const handleDynamicLabelAdd = () => {
    onChange([
      ...labels,
      {
        key: { id: undefined, name: undefined, prescribed: false },
        value: { id: null, name: undefined, prescribed: false }, // id = null means it's a templated value
      },
    ]);
  };

  const onLoadKeys = async (search?: string) => {
    let result = undefined;

    try {
      result = await labelsStore.loadKeys(search);
    } catch (error) {
      openErrorNotification('There was an error processing your request. Please try again');
    }

    const groups = splitToGroups(result);

    return groups;
  };

  const onLoadValuesForKey = async (key: string, search?: string) => {
    let result = undefined;

    try {
      const { values } = await labelsStore.loadValuesForKey(key, search);
      result = values;
    } catch (error) {
      openErrorNotification('There was an error processing your request. Please try again');
    }

    const groups = splitToGroups(result);

    return groups;
  };

  return (
    <VerticalGroup>
      <ServiceLabels
        isAddingDisabled
        loadById
        inputWidth={INPUT_WIDTH}
        errors={labelErrors}
        value={labels}
        onLoadKeys={onLoadKeys}
        onLoadValuesForKey={onLoadValuesForKey}
        onCreateKey={labelsStore.createKey}
        onUpdateKey={labelsStore.updateKey}
        onCreateValue={labelsStore.createValue}
        onUpdateValue={labelsStore.updateKeyValue}
        onUpdateError={(res) => {
          if (res?.response?.status === 409) {
            openErrorNotification(`Duplicate values are not allowed`);
          } else {
            openErrorNotification(GENERIC_ERROR);
          }
        }}
        renderValue={(option, index, renderValueDefault) => {
          if (option.value.id === null) {
            return (
              <Input
                placeholder="Jinja2 template"
                autoFocus
                disabled={!labels[index].key.id}
                width={INPUT_WIDTH / 8}
                value={option.value.name}
                addonAfter={
                  <Button
                    variant="secondary"
                    icon="edit"
                    onClick={() => {
                      onShowTemplateEditor(index);
                    }}
                  />
                }
                onChange={(e: ChangeEvent<HTMLInputElement>) => {
                  const labelsList = [...labels];
                  labelsList[index].value.name = e.currentTarget.value;
                  onChange([...labelsList]);
                }}
              />
            );
          } else {
            return renderValueDefault(option, index);
          }
        }}
        onDataUpdate={(value) => {
          onChange([...value]);
        }}
        getIsKeyEditable={(option) => !option.prescribed}
        getIsValueEditable={(option) => !option.prescribed}
      />

      <Dropdown
        overlay={
          <Menu>
            <Menu.Item label="Static label" onClick={handleStaticLabelAdd} />
            <Menu.Item label="Dynamic label" onClick={handleDynamicLabelAdd} />
          </Menu>
        }
      >
        <Button variant="secondary" icon="plus" disabled={getIsAddBtnDisabled(labels)}>
          Add label
        </Button>
      </Dropdown>
    </VerticalGroup>
  );
};

export const getIsAddBtnDisabled = (labels) => {
  const lastItem = labels.at(-1);
  return lastItem && (lastItem?.key.id === undefined || lastItem?.value.id === undefined);
};
