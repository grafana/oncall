import React, { useState } from 'react';

import { Alert, Button, Field, HorizontalGroup, Input, Modal, VerticalGroup } from '@grafana/ui';

interface EditModalProps {
  isInUse;
  onDismiss(): void;
  isKeyEdit: boolean;
  keyString: string;
  valueString: string;
  onKeyUpdate(newKey: string): void;
  onValueUpdate(value: string): void;
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
    <Modal
      isOpen
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
