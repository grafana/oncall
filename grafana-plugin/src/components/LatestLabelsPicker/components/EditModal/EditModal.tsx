import { Alert, Button, Field, HorizontalGroup, Input, Modal, VerticalGroup } from '@grafana/ui';
import React, { useState } from 'react';
import { ItemSelected } from 'components/LatestLabelsPicker/core/types';
import { openErrorNotification } from 'utils';

export interface BaseEditModal {
  isKeyEdit: boolean;
  isOpen: boolean;
  option: ItemSelected;
  rowIndex: number;
  isInUse?: boolean;
}

export interface EditModalProps extends BaseEditModal {
  onDismiss(): void;
  onKeyUpdate(keyId: string, keyName: string, rowIndex: number): Promise<void>;
  onValueUpdate(keyId: string, valueId: string, value: string, rowIndex: number): Promise<void>;
}

const FieldId = 'id';
const FieldName = 'repr';

const EditModal: React.FC<EditModalProps> = ({
  isKeyEdit,
  isOpen,
  option,
  onDismiss,
  isInUse,
  rowIndex,
  onKeyUpdate,
  onValueUpdate,
}) => {
  const [keyField, setKeyField] = useState<string>(option?.key[FieldName]);
  const [valueField, setValueField] = useState<string>(option?.value[FieldName]);

  return (
    <Modal
      isOpen={isOpen}
      title={<h2 className="pair-heading">{isKeyEdit ? 'Edit Key' : 'Edit Value'}</h2>}
      onDismiss={onDismiss}
    >
      {isKeyEdit ? renderKeyEdit() : renderValueEdit()}
    </Modal>
  );

  function renderKeyEdit() {
    return (
      <VerticalGroup>
        {isInUse && (
          <Alert severity="warning" title="This label is in use. The change will impact all other implementations." />
        )}

        <Field label="Key" className="pair-width-100">
          <Input
            value={keyField}
            onChange={(ev: React.ChangeEvent<HTMLInputElement>) => setKeyField(ev.target.value)}
          />
        </Field>

        <HorizontalGroup justify="flex-end">
          <Button variant="secondary" onClick={onDismiss}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={() => onKeyUpdate(option.key[FieldId], keyField, rowIndex).catch(onSaveError)}
          >
            Update
          </Button>
        </HorizontalGroup>
      </VerticalGroup>
    );
  }

  function renderValueEdit() {
    return (
      <VerticalGroup spacing="md">
        <div className="pair-flex">
          <Field label="Key" className="pair-width-100">
            <Input value={keyField} disabled />
          </Field>
          <Field label="Value" className="pair-width-100">
            <Input
              value={valueField}
              placeholder="Type in the value for this key"
              onChange={(ev: React.ChangeEvent<HTMLInputElement>) => setValueField(ev.target.value)}
            />
          </Field>
        </div>

        <HorizontalGroup justify="flex-end">
          <Button variant="secondary" onClick={onDismiss}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={() =>
              onValueUpdate(option.key[FieldId], option.value[FieldId], valueField, rowIndex).catch(onSaveError)
            }
          >
            Update
          </Button>
        </HorizontalGroup>
      </VerticalGroup>
    );
  }

  function onSaveError(res) {
    if (res?.response?.status === 409) {
      openErrorNotification(`Duplicate values are not allowed`);
    }
  }
};

export default EditModal;
