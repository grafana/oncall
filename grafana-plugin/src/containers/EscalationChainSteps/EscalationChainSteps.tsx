import React, { ReactElement, useCallback, useEffect } from 'react';

import { LoadingPlaceholder, Select } from '@grafana/ui';
import cn from 'classnames/bind';
import { get } from 'lodash-es';
import { observer } from 'mobx-react';

import EscalationPolicy from 'components/Policy/EscalationPolicy';
import SortableList from 'components/SortableList/SortableList';
import Timeline from 'components/Timeline/Timeline';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { EscalationChain } from 'models/escalation_chain/escalation_chain.types';
import { EscalationPolicyOption } from 'models/escalation_policy/escalation_policy.types';
import { useStore } from 'state/useStore';
import { getVar } from 'utils/DOM';
import { UserActions } from 'utils/authorization';

import styles from './EscalationChainSteps.module.css';

const cx = cn.bind(styles);

interface EscalationChainStepsProps {
  id: EscalationChain['id'];
  isDisabled?: boolean;
  addonBefore?: ReactElement;
  offset?: number;
}

const EscalationChainSteps = observer((props: EscalationChainStepsProps) => {
  const { id, offset = 0, isDisabled = false, addonBefore } = props;

  const store = useStore();

  const { escalationPolicyStore } = store;

  useEffect(() => {
    escalationPolicyStore.updateEscalationPolicies(id);
  }, [id]);

  const handleSortEnd = useCallback(
    ({ oldIndex, newIndex }: any) => {
      escalationPolicyStore.moveEscalationPolicyToPosition(oldIndex, newIndex, id);
    },
    [id]
  );

  const handleCreateEscalationStep = useCallback(
    async (option: EscalationPolicyOption) => {
      await escalationPolicyStore.createEscalationPolicy(id, {
        step: option.value,
      });

      escalationPolicyStore.updateEscalationPolicies(id);
    },
    [id]
  );

  const escalationPolicyIds = escalationPolicyStore.escalationChainToEscalationPolicy[id];
  const isSlackInstalled = Boolean(store.organizationStore.currentOrganization?.slack_team_identity);

  return (
    // @ts-ignore
    <SortableList useDragHandle className={cx('steps')} axis="y" lockAxis="y" onSortEnd={handleSortEnd}>
      {addonBefore}
      {escalationPolicyIds ? (
        escalationPolicyIds.map((escalationPolicyId, index) => {
          const COLOR_RED = '#E60000';
          const STEP_COLORS = ['#1A7F4B', '#33cc33', '#ffbf00', '#FF8000', COLOR_RED];

          const { escalationPolicyStore } = store;
          const escalationPolicy = escalationPolicyStore.items[escalationPolicyId];

          if (!escalationPolicy) {
            return null;
          }

          return (
            <EscalationPolicy
              index={index} // This in here is a MUST for the SortableElement
              key={`item-${escalationPolicy.id}`}
              data={escalationPolicy}
              number={index + offset + 1}
              backgroundColor={isDisabled ? getVar('--tag-background-success') : STEP_COLORS[index] || COLOR_RED}
              escalationChoices={escalationPolicyStore.webEscalationChoices}
              waitDelays={get(escalationPolicyStore.escalationChoices, 'wait_delay.choices', [])}
              numMinutesInWindowOptions={escalationPolicyStore.numMinutesInWindowOptions}
              onChange={escalationPolicyStore.saveEscalationPolicy.bind(escalationPolicyStore)}
              onDelete={escalationPolicyStore.deleteEscalationPolicy.bind(escalationPolicyStore)}
              isSlackInstalled={isSlackInstalled}
              teamStore={store.grafanaTeamStore}
              scheduleStore={store.scheduleStore}
              outgoingWebhookStore={store.outgoingWebhookStore}
              isDisabled={isDisabled}
            />
          );
        })
      ) : (
        <LoadingPlaceholder text="Loading..." />
      )}
      {!isDisabled && (
        <Timeline.Item
          number={(escalationPolicyIds?.length || 0) + offset + 1}
          backgroundColor={isDisabled ? getVar('--tag-background-success') : getVar('--tag-secondary')}
          textColor={isDisabled ? getVar('--tag-text-success') : undefined}
        >
          <WithPermissionControlTooltip userAction={UserActions.EscalationChainsWrite}>
            <Select
              isSearchable
              menuShouldPortal
              placeholder="Add escalation step..."
              onChange={handleCreateEscalationStep}
              options={escalationPolicyStore.webEscalationChoices.map((choice: EscalationPolicyOption) => ({
                value: choice.value,
                label: choice.create_display_name,
              }))}
              value={null}
            />
          </WithPermissionControlTooltip>
        </Timeline.Item>
      )}
    </SortableList>
  );
});

export default EscalationChainSteps;
