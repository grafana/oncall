import React, { ChangeEvent, FC, useCallback, useState } from 'react';

import { Button, Field, HorizontalGroup, Input, Modal } from '@grafana/ui';
import cn from 'classnames/bind';

import { GSelect } from 'containers/GSelect/GSelect';
import { EscalationChain } from 'models/escalation_chain/escalation_chain.types';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import { useStore } from 'state/useStore';
import { openWarningNotification } from 'utils/utils';

import styles from 'containers/EscalationChainForm/EscalationChainForm.module.css';
import { Controller, Form, FormProvider, useForm } from 'react-hook-form';

export enum EscalationChainFormMode {
  Create = 'Create',
  Copy = 'Copy',
  Update = 'Update',
}

interface EscalationChainFormProps {
  escalationChainId?: EscalationChain['id'];
  mode: EscalationChainFormMode;
  onHide: () => void;
  onSubmit: (id: EscalationChain['id']) => Promise<void>;
}

interface EscalationFormFields {
  team: string;
  name: string;
}

const cx = cn.bind(styles);

export const EscalationChainForm: FC<EscalationChainFormProps> = (props) => {
  const { escalationChainId, onHide, onSubmit: onSubmitProp, mode } = props;

  const store = useStore();
  const { escalationChainStore, userStore, grafanaTeamStore } = store;

  const user = userStore.currentUser;

  const escalationChain = escalationChainId ? escalationChainStore.items[escalationChainId] : undefined;

  const [name, setName] = useState<string | undefined>(
    mode === EscalationChainFormMode.Copy ? `${escalationChain?.name} copy` : escalationChain?.name
  );

  const formMethods = useForm<EscalationFormFields>({
    mode: 'onChange',
    defaultValues: {
      team: escalationChain?.team || user.current_team,
    },
  });

  const {
    control,
    getValues,
    formState: { errors },
    handleSubmit,
  } = formMethods;

  const teamName = getValues('team');

  const onSubmit = useCallback(async () => {
    console.log('here');
    return;
    let escalationChain: EscalationChain | void;

    const isCreateMode = mode === EscalationChainFormMode.Create;
    const isCopyMode = mode === EscalationChainFormMode.Copy;

    if (isCreateMode) {
      escalationChain = await escalationChainStore.create<EscalationChain>({ name, team: teamName });
    } else if (isCopyMode) {
      escalationChain = await escalationChainStore.clone(escalationChainId, { name, team: teamName });
    } else {
      escalationChain = await escalationChainStore.update<EscalationChain>(escalationChainId, {
        name,
        team: teamName,
      });
    }

    if (!escalationChain) {
      let verb: string;

      if (isCreateMode) {
        verb = 'creating';
      } else if (isCopyMode) {
        verb = 'copying';
      } else {
        verb = 'updating';
      }

      openWarningNotification(`There was an issue ${verb} the escalation chain. Please try again`);
      return;
    }

    try {
      await onSubmitProp(escalationChain.id);
      onHide();
    } catch (err) {
      // setErrors({
      //   name: err.response.data.name || err.response.data.detail || err.response.data.non_field_errors,
      // });
    }
  }, [name, teamName, mode, onSubmitProp]);

  const handleNameChange = useCallback((event: ChangeEvent<HTMLInputElement>) => {
    setName(event.target.value);
  }, []);

  return (
    <Modal isOpen title={`${mode} Escalation Chain`} onDismiss={onHide}>
      <div className={cx('root')}>
        <FormProvider {...formMethods}>
          <form onSubmit={handleSubmit(onSubmit)}>
            <Controller
              name={'team'}
              control={control}
              rules={{ required: 'Team is required' }}
              render={({ field }) => (
                <Field label="Assign to team">
                  <GSelect<GrafanaTeam>
                    {...field}
                    items={grafanaTeamStore.items}
                    fetchItemsFn={grafanaTeamStore.updateItems}
                    fetchItemFn={grafanaTeamStore.fetchItemById}
                    getSearchResult={grafanaTeamStore.getSearchResult}
                    displayField="name"
                    valueField="id"
                    allowClear
                    placeholder="Select a team"
                    className={cx('team-select')}
                    onChange={(value) => {
                      field.onChange(value);
                    }}
                  />
                </Field>
              )}
            />

            <Controller
              name={'name'}
              control={control}
              rules={{ required: 'Name is required' }}
              render={({ field }) => (
                <Field
                  invalid={Boolean(errors['name'])}
                  error={errors['name']?.message}
                  label="Escalation Chain name"
                  data-testid="create-escalation-chain-name-input-modal"
                >
                  <Input autoFocus {...field} />
                </Field>
              )}
            />

            <HorizontalGroup justify="flex-end">
              <Button variant="secondary" onClick={onHide}>
                Cancel
              </Button>
              <Button type="submit" variant="primary">
                {`${mode} Escalation Chain`}
              </Button>
            </HorizontalGroup>
          </form>
        </FormProvider>
      </div>
    </Modal>
  );
};
