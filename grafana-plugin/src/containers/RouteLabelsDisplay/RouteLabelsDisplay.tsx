import React, { ChangeEvent } from 'react';

import { ServiceLabels } from '@grafana/labels';
import { Button, Dropdown, Input, Menu, VerticalGroup } from '@grafana/ui';

import { splitToGroups } from 'models/label/label.helpers';
import { components } from 'network/oncall-api/autogenerated-api.types';
import { useStore } from 'state/useStore';
import { GENERIC_ERROR } from 'utils/consts';
import { openErrorNotification } from 'utils/utils';

interface RouteLabelsDisplayProps {
  labels: Array<components['schemas']['LabelPair']>;
  labelErrors: any;
  onChange: (value: Array<components['schemas']['LabelPair']>) => void;
  onShowTemplateEditor: (index: number) => void;
}

const INPUT_WIDTH = 280;
const DUPLICATE_ERROR = 'Duplicate values are not allowed';

export const RouteLabelsDisplay: React.FC<RouteLabelsDisplayProps> = ({
  labels,
  labelErrors,
  onChange,
  onShowTemplateEditor,
}) => {
  const { labelsStore } = useStore();

  const onLabelAdd = (isDynamic = false) => {
    onChange([
      ...labels,
      {
        key: { id: undefined, name: undefined, prescribed: false },
        // id = null being a templated value
        value: { id: isDynamic ? null : undefined, name: undefined, prescribed: false },
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

    return splitToGroups(result);
  };

  const onLoadValuesForKey = async (key: string, search?: string) => {
    let result = undefined;

    try {
      const { values } = await labelsStore.loadValuesForKey(key, search);
      result = values;
    } catch (error) {
      openErrorNotification('There was an error processing your request. Please try again');
    }

    return splitToGroups(result);
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
            openErrorNotification(DUPLICATE_ERROR);
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
                    disabled={!labels[index].key.id}
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
            <Menu.Item label="Static label" onClick={() => onLabelAdd(false)} />
            <Menu.Item label="Dynamic label" onClick={() => onLabelAdd(true)} />
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

const getIsAddBtnDisabled = (labels: Array<components['schemas']['LabelPair']> = []) => {
  const lastItem = labels.at(-1);
  return lastItem && (lastItem.key?.id === undefined || lastItem.value?.id === undefined);
};
