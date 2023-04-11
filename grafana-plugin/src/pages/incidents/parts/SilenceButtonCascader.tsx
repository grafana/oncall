import React from 'react';

import { ButtonCascader, ComponentSize } from '@grafana/ui';
import { observer } from 'mobx-react';

import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { SelectOption } from 'state/types';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization';

interface SilenceButtonCascaderProps {
  className?: string;
  disabled?: boolean;
  buttonSize?: string;

  onSelect: (value: number) => void;
}

export const SilenceButtonCascader = observer((props: SilenceButtonCascaderProps) => {
  const { onSelect, className, disabled = false, buttonSize } = props;
  const { alertGroupStore } = useStore();

  const silenceOptions = alertGroupStore.silenceOptions || [];

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

  function getOptions() {
    return silenceOptions.map((silenceOption: SelectOption) => ({
      value: silenceOption.value,
      label: silenceOption.display_name,
    }));
  }
});
