import React, { ReactElement, useCallback, useEffect } from 'react';

import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { LoadingPlaceholder, Select, useStyles2, useTheme2 } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import { getLabelBackgroundTextColorObject } from 'styles/utils.styles';

import { EscalationPolicy, EscalationPolicyProps } from 'components/Policy/EscalationPolicy';
import { SortableList } from 'components/SortableList/SortableList';
import { Timeline } from 'components/Timeline/Timeline';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { EscalationChain } from 'models/escalation_chain/escalation_chain.types';
import { EscalationPolicyOption } from 'models/escalation_policy/escalation_policy.types';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization/authorization';

import styles from './EscalationChainSteps.module.css';

const cx = cn.bind(styles);

interface EscalationChainStepsProps {
  id: EscalationChain['id'];
  isDisabled?: boolean;
  addonBefore?: ReactElement;
  offset?: number;
}

const getStyles = (theme: GrafanaTheme2) => {
  return {
    background: css`
      background-color: ${theme.colors.success.main};
    `,
  };
};

export const EscalationChainSteps = observer((props: EscalationChainStepsProps) => {
  const { id, offset = 0, isDisabled = false, addonBefore } = props;

  const store = useStore();
  const styles = useStyles2(getStyles);
  const theme = useTheme2();

  const { escalationPolicyStore } = store;

  useEffect(() => {
    escalationPolicyStore.updateEscalationPolicies(id);
  }, [id]);

  useEffect(() => {
    escalationPolicyStore.updateWebEscalationPolicyOptions();
  }, []);

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
  const { bgColor: successBgColor, textColor: successTextColor } = getLabelBackgroundTextColorObject('green', theme);

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

          const extraProps: Partial<EscalationPolicyProps> = {};
          if (isDisabled) {
            extraProps.backgroundClassName = styles.background;
          } else {
            extraProps.backgroundHexNumber = STEP_COLORS[index] || COLOR_RED;
          }

          return (
            <EscalationPolicy
              index={index} // This in here is a MUST for the SortableElement
              key={`item-${escalationPolicy.id}`}
              data={escalationPolicy}
              number={index + offset + 1}
              escalationChoices={escalationPolicyStore.webEscalationChoices}
              onChange={escalationPolicyStore.saveEscalationPolicy.bind(escalationPolicyStore)}
              onDelete={escalationPolicyStore.deleteEscalationPolicy.bind(escalationPolicyStore)}
              isSlackInstalled={isSlackInstalled}
              isDisabled={isDisabled}
              {...extraProps}
            />
          );
        })
      ) : (
        <LoadingPlaceholder text="Loading..." />
      )}
      {!isDisabled && (
        <Timeline.Item
          number={(escalationPolicyIds?.length || 0) + offset + 1}
          backgroundHexNumber={isDisabled ? successBgColor : theme.colors.secondary.main}
          textColor={isDisabled ? successTextColor : undefined}
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
