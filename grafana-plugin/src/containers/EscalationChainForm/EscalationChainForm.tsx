import React, { ChangeEvent, FC, useCallback, useState } from 'react';

import { Button, Field, HorizontalGroup, Input, Modal } from '@grafana/ui';
import cn from 'classnames/bind';

import { EscalationChain } from 'models/escalation_chain/escalation_chain.types';
import { useStore } from 'state/useStore';

import styles from 'containers/EscalationChainForm/EscalationChainForm.module.css';

interface EscalationChainFormProps {
  escalationChainId?: EscalationChain['id'];
  onHide: () => void;
  onUpdate: (id: EscalationChain['id']) => void;
}

const cx = cn.bind(styles);

const EscalationChainForm: FC<EscalationChainFormProps> = ({ escalationChainId, onHide, onUpdate }) => {
  const { escalationChainStore } = useStore();
  const escalationChain = escalationChainId ? escalationChainStore.items[escalationChainId] : undefined;

  const [name, setName] = useState<string | undefined>(escalationChain?.name);
  const [errors, setErrors] = useState<{ [key: string]: string }>({});

  const onCreateClickCallback = useCallback(() => {
    (escalationChainId
      ? escalationChainStore.clone(escalationChainId, { name })
      : escalationChainStore.create({ name })
    )
      .then((escalationChain: EscalationChain) => {
        onUpdate(escalationChain.id);

        onHide();
      })
      .catch((data) => {
        setErrors({
          name: data.response.data.name || data.response.data.detail || data.response.data.non_field_errors,
        });
      });
  }, [name]);

  const handleNameChange = useCallback((event: ChangeEvent<HTMLInputElement>) => {
    setName(event.target.value);
  }, []);

  return (
    <Modal
      isOpen
      title={escalationChainId ? `Copy ${escalationChain.name}` : `New Escalation Chain`}
      onDismiss={onHide}
    >
      <div className={cx('root')}>
        <Field invalid={Boolean(errors['name'])} error={errors['name']} label="Escalation Chain name">
          <Input autoFocus value={name} onChange={handleNameChange} />
        </Field>
        <HorizontalGroup justify="flex-end">
          <Button variant="secondary" onClick={onHide}>
            Cancel
          </Button>
          <Button variant="primary" onClick={onCreateClickCallback}>
            {escalationChainId ? 'Copy' : 'Create'}
          </Button>
        </HorizontalGroup>
      </div>
    </Modal>
  );
};

export default EscalationChainForm;
