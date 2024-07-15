import React, { FC } from 'react';

import { Button, Field, HorizontalGroup, Input, Modal } from '@grafana/ui';
import cn from 'classnames/bind';
import { Controller, FormProvider, useForm } from 'react-hook-form';

import { GSelect } from 'containers/GSelect/GSelect';
import { EscalationChain } from 'models/escalation_chain/escalation_chain.types';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import { useStore } from 'state/useStore';
import { openWarningNotification } from 'utils/utils';

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
  onSubmit: (id: EscalationChain['id']) => Promise<void>;
}

interface EscalationFormFields {
  team: string;
  name: string;
}

const cx = cn.bind(styles);

export const EscalationChainForm: FC<EscalationChainFormProps> = (props) => {
  const store = useStore();

  const { escalationChainId, onHide, onSubmit: onSubmitProp, mode } = props;
  const { escalationChainStore, userStore, grafanaTeamStore } = store;

  const user = userStore.currentUser;
  const escalationChain = escalationChainId ? escalationChainStore.items[escalationChainId] : undefined;
  const isCreateMode = mode === EscalationChainFormMode.Create;
  const isCopyMode = mode === EscalationChainFormMode.Copy;

  const formMethods = useForm<EscalationFormFields>({
    mode: 'onChange',
    defaultValues: {
      team: escalationChain?.team || user.current_team,
      name: isCopyMode ? `${escalationChain.name} copy` : '',
    },
  });

  const {
    control,
    setError,
    getValues,
    formState: { errors },
    handleSubmit,
  } = formMethods;

  return (
    <Modal isOpen title={`${mode} Escalation Chain`} onDismiss={onHide}>
      <div className={cx('root')}>
        <FormProvider {...formMethods}>
          <form onSubmit={handleSubmit(onSubmit)}>
            <Controller
              name={'team'}
              control={control}
              render={({ field }) => (
                <Field label="Assign to team" invalid={Boolean(errors['team'])} error={errors['team']?.message}>
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

  async function onSubmit() {
    let escalationChain: EscalationChain | void;

    const teamName = getValues('team');
    const escalationChainName = getValues('name');

    try {
      if (isCreateMode) {
        escalationChain = await escalationChainStore.create<EscalationChain>({
          name: escalationChainName,
          team: teamName,
        });
      } else if (isCopyMode) {
        escalationChain = await escalationChainStore.clone(escalationChainId, {
          name: escalationChainName,
          team: teamName,
        });
      } else {
        escalationChain = await escalationChainStore.update<EscalationChain>(escalationChainId, {
          name: escalationChainName,
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

      await onSubmitProp(escalationChain.id);
      onHide();
    } catch (err) {
      if (err?.response?.data) {
        const keys = Object.keys(err.response.data);
        keys.forEach((key: keyof EscalationFormFields) => {
          const message = Array.isArray(err.response.data[key]) ? err.response.data[key][0] : err.response.data[key];
          setError('name', { message });
        });
      }
    }
  }
};
