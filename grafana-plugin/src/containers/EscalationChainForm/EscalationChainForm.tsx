import React, { ChangeEvent, FC, useCallback, useState } from 'react';

import { Button, Field, HorizontalGroup, Input, Modal } from '@grafana/ui';
import cn from 'classnames/bind';

import GSelect from 'containers/GSelect/GSelect';
import { EscalationChain } from 'models/escalation_chain/escalation_chain.types';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import { useStore } from 'state/useStore';

import styles from 'containers/EscalationChainForm/EscalationChainForm.module.css';

export enum EscalationChainFormMode {
  Create = 'Create',
  Copy = 'Copy',
  Update = 'Update',
}

interface EscalationChainFormProps {
  escalationChainId?: EscalationChain['id'];
  mode: EscalationChainFormMode;
  onHide: () => void;
  onUpdate: (id: EscalationChain['id']) => void;
}

const cx = cn.bind(styles);

const EscalationChainForm: FC<EscalationChainFormProps> = (props) => {
  const { escalationChainId, onHide, onUpdate, mode } = props;

  const store = useStore();
  const { escalationChainStore, userStore } = store;

  const user = userStore.currentUser;

  const escalationChain = escalationChainId ? escalationChainStore.items[escalationChainId] : undefined;

  const [name, setName] = useState<string | undefined>(
    mode === EscalationChainFormMode.Copy ? `${escalationChain?.name} copy` : escalationChain?.name
  );
  const [selectedTeam, setSelectedTeam] = useState<GrafanaTeam['id']>(escalationChain?.team || user.current_team);
  const [errors, setErrors] = useState<{ [key: string]: string }>({});

  const onCreateClickCallback = useCallback(() => {
    const promise =
      mode === EscalationChainFormMode.Create
        ? escalationChainStore.create({ name, team: selectedTeam })
        : mode === EscalationChainFormMode.Copy
        ? escalationChainStore.clone(escalationChainId, { name, team: selectedTeam })
        : escalationChainStore.update(escalationChainId, { name, team: selectedTeam });

    promise
      .then((escalationChain: EscalationChain) => {
        onUpdate(escalationChain.id);

        onHide();
      })
      .catch((data) => {
        setErrors({
          name: data.response.data.name || data.response.data.detail || data.response.data.non_field_errors,
        });
      });
  }, [name, selectedTeam, mode]);

  const handleNameChange = useCallback((event: ChangeEvent<HTMLInputElement>) => {
    setName(event.target.value);
  }, []);

  return (
    <Modal isOpen title={`${mode} Escalation Chain`} onDismiss={onHide}>
      <div className={cx('root')}>
        <Field label="Assign to team">
          <GSelect
            modelName="grafanaTeamStore"
            displayField="name"
            valueField="id"
            showSearch
            allowClear
            placeholder="Select a team"
            className={cx('team-select')}
            onChange={setSelectedTeam}
            value={selectedTeam}
          />
        </Field>
        <Field
          invalid={Boolean(errors['name'])}
          error={errors['name']}
          label="Escalation Chain name"
          data-testid="create-escalation-chain-name-input-modal"
        >
          <Input autoFocus value={name} onChange={handleNameChange} />
        </Field>
        <HorizontalGroup justify="flex-end">
          <Button variant="secondary" onClick={onHide}>
            Cancel
          </Button>
          <Button variant="primary" onClick={onCreateClickCallback}>
            {`${mode} Escalation Chain`}
          </Button>
        </HorizontalGroup>
      </div>
    </Modal>
  );
};

export default EscalationChainForm;
