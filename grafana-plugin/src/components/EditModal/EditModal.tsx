import React, { useState } from 'react';

import { css } from '@emotion/css';
import { Alert, Button, Field, HorizontalGroup, Input, Modal, VerticalGroup, useStyles2 } from '@grafana/ui';
import { KEY_ERROR_MESSAGE, VALUE_ERROR_MESSAGE } from 'core/consts';
import { ItemSelected, LabelInputType, ServiceLabelValidator } from 'core/types';

export interface BaseEditModal {
  isKeyEdit: boolean;
  isOpen: boolean;
  option: ItemSelected;
  rowIndex: number;
}

export interface EditModalProps extends BaseEditModal {
  valueField: string;
  labelField: string;

  onDismiss(): void;
  onUpdateError(res: any): void;
  onKeyUpdate(keyId: string, keyName: string, rowIndex: number): Promise<void>;
  onValueUpdate(keyId: string, valueId: string, value: string, rowIndex: number): Promise<void>;

  validateUserInput?: (fieldValue: string, type: LabelInputType) => ServiceLabelValidator;
}

export const EditModal: React.FC<EditModalProps> = ({
  isKeyEdit,
  isOpen,
  option,
  onDismiss,
  rowIndex,
  onKeyUpdate,
  onValueUpdate,
  onUpdateError,
  validateUserInput,

  valueField: FieldId,
  labelField: FieldName,
}) => {
  const styles = useStyles2(() => getStyles());

  const [keyField, setKeyField] = useState<string>(option?.key[FieldName]);
  const [valueField, setValueField] = useState<string>(option?.value[FieldName]);

  return (
    <Modal
      isOpen={isOpen}
      title={<h2 className={styles.header}>{isKeyEdit ? 'Edit Key' : 'Edit Value'}</h2>}
      onDismiss={onDismiss}
    >
      {isKeyEdit ? renderKeyEdit() : renderValueEdit()}
    </Modal>
  );

  function getStyles() {
    return {
      header: css`
        font-size: 18px;
      `,
      fullWidth: css`
        width: 100%;
      `,
      flex: css`
        display: flex;
        flex-direction: row;
        width: 100%;
        gap: 4px;
      `,
    };
  }

  function renderKeyEdit() {
    const fieldValidation = validateUserInput(keyField, LabelInputType.key);
    const errorMessage = fieldValidation.errorMessage || KEY_ERROR_MESSAGE;

    return (
      <VerticalGroup>
        {<Alert severity="warning" title="This label is in use. The change will impact all other implementations." />}

        <Field label="Key" className={styles.fullWidth} invalid={!fieldValidation.isValid} error={errorMessage}>
          <Input
            value={keyField}
            onChange={(ev: React.ChangeEvent<HTMLInputElement>) => setKeyField(ev.target.value)}
          />
        </Field>

        <HorizontalGroup justify="flex-end">
          <Button variant="secondary" onClick={onDismiss}>
            Cancel
          </Button>
          <Button variant="primary" disabled={!fieldValidation.isValid} onClick={onUpdate}>
            Update
          </Button>
        </HorizontalGroup>
      </VerticalGroup>
    );

    function onUpdate() {
      if (fieldValidation.isValid) {
        onKeyUpdate(option.key[FieldId], keyField, rowIndex).catch(onUpdateError);
      }
    }
  }

  function renderValueEdit() {
    const fieldValidation = validateUserInput(valueField, LabelInputType.value);
    const errorMessage = fieldValidation.errorMessage || VALUE_ERROR_MESSAGE;

    return (
      <VerticalGroup spacing="md">
        <div className={styles.flex}>
          <Field label="Key" className={styles.fullWidth}>
            <Input value={keyField} disabled />
          </Field>
          <Field label="Value" className={styles.fullWidth} invalid={!fieldValidation.isValid} error={errorMessage}>
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
          <Button variant="primary" disabled={!fieldValidation} onClick={onUpdate}>
            Update
          </Button>
        </HorizontalGroup>
      </VerticalGroup>
    );

    function onUpdate() {
      if (fieldValidation.isValid) {
        onValueUpdate(option.key[FieldId], option.value[FieldId], valueField, rowIndex).catch(onUpdateError);
      }
    }
  }
};
