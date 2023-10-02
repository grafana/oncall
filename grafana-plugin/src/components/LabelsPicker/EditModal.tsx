import React, { useState } from 'react';

import { Alert, Button, Field, HorizontalGroup, Input, Modal, VerticalGroup } from '@grafana/ui';

import './styles.css';

interface EditModalProps {
  isInUse;
  onDismiss(): void;
  isKeyEdit: boolean;
  keyString: string;
  onKeyUpdate?(newKey: string): void;
  valueString?: string;
  onValueUpdate?(value: string): void;
}

const EditModal: React.FC<EditModalProps> = ({
  isKeyEdit,
  onDismiss,
  isInUse,
  keyString,
  valueString,
  onKeyUpdate,
  onValueUpdate,
}) => {
  const [keyField, setKeyField] = useState<string>(keyString);
  const [valueField, setValueField] = useState<string>(valueString);

  return (
    <Modal className="labels-edit-modal" isOpen title={isKeyEdit ? 'Edit Key' : 'Edit Value'} onDismiss={onDismiss}>
      {isKeyEdit ? renderKeyEdit() : renderValueEdit()}
    </Modal>
  );

  function renderKeyEdit() {
    return (
      <VerticalGroup>
        {isInUse && (
          <Alert severity="warning" title="This label is in use. The change will impact all other implementations." />
        )}

        <Field label="Key">
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
            onClick={() => {
              onKeyUpdate(keyField);
              onDismiss();
            }}
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
        <div>
          <Field label="Key">
            <Input value={keyField} disabled />
          </Field>
          <Field label="Value">
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
            onClick={() => {
              onValueUpdate(valueField);
              onDismiss();
            }}
          >
            Update
          </Button>
        </HorizontalGroup>
      </VerticalGroup>
    );
  }
};

export default EditModal;
