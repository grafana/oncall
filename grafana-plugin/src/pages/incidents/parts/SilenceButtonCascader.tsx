import React from 'react';

import { ButtonCascader, CascaderOption, ComponentSize } from '@grafana/ui';
import { observer } from 'mobx-react';

import { SILENCE_DURATION_LIST } from 'components/Policy/Policy.consts';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { UserActions } from 'utils/authorization/authorization';

interface SilenceButtonCascaderProps {
  className?: string;
  disabled?: boolean;
  buttonSize?: string;

  onSelect: (value: number) => void;
}

export const SilenceButtonCascader = observer((props: SilenceButtonCascaderProps) => {
  const { onSelect, className, disabled = false, buttonSize } = props;

  return (
    <WithPermissionControlTooltip key="silence" userAction={UserActions.AlertGroupsWrite}>
      <ButtonCascader
        variant="secondary"
        className={className}
        disabled={disabled}
        onChange={(value) => onSelect(Number(value))}
        options={getOptions()}
        value={undefined}
        buttonProps={{ size: buttonSize as ComponentSize }}
      >
        Silence
      </ButtonCascader>
    </WithPermissionControlTooltip>
  );

  function getOptions(): CascaderOption[] {
    return [...SILENCE_DURATION_LIST] as CascaderOption[];
  }
});
