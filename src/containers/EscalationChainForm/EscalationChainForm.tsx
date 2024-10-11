import React, { FC } from 'react';

import { css, cx } from '@emotion/css';
import { Button, Field, Input, Modal, Stack } from '@grafana/ui';
import { openWarningNotification } from 'helpers/helpers';
import { observer } from 'mobx-react';
import { Controller, FormProvider, useForm } from 'react-hook-form';

import { GSelect } from 'containers/GSelect/GSelect';
import { EscalationChain } from 'models/escalation_chain/escalation_chain.types';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import { useStore } from 'state/useStore';

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

export const EscalationChainForm: FC<EscalationChainFormProps> = observer((props) => {
  const { escalationChainId, onHide, onSubmit: onSubmitProp, mode } = props;

  const store = useStore();
  const {
    escalationChainStore,
    userStore,
    grafanaTeamStore,
    // dereferencing items is needed to rerender GSelect
    grafanaTeamStore: { items: grafanaTeamItems },
  } = store;

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
      <div
        className={css`
          display: block;
        `}
      >
        <FormProvider {...formMethods}>
          <form onSubmit={handleSubmit(onSubmit)}>
            <Controller
              name={'team'}
              control={control}
              render={({ field }) => (
                <Field label="Assign to team" invalid={Boolean(errors['team'])} error={errors['team']?.message}>
                  <GSelect<GrafanaTeam>
                    {...field}
                    items={grafanaTeamItems}
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

            <Stack justifyContent="flex-end">
              <Button variant="secondary" onClick={onHide}>
                Cancel
              </Button>
              <Button type="submit" variant="primary">
                {`${mode} Escalation Chain`}
              </Button>
            </Stack>
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
});
