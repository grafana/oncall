import React, { useCallback } from 'react';

import { ButtonCascader } from '@grafana/ui';
import { ComponentSize } from '@grafana/ui/types/size';
import { observer } from 'mobx-react';

import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { SelectOption } from 'state/types';
import { useStore } from 'state/useStore';
import { UserAction } from 'state/userAction';

interface SilenceDropdownProps {
  onSelect: (value: number) => void;
  className?: string;
  disabled?: boolean;
  buttonSize?: string;
}

const SilenceDropdown = observer(({ onSelect, className, disabled = false, buttonSize }: SilenceDropdownProps) => {
  const { alertGroupStore } = useStore();
  const silenceOptions = alertGroupStore.silenceOptions || [];

  const onSelectCallback = useCallback(
    ([value]) => {
      onSelect(Number(value));
    },
    [onSelect]
  );

  return (
    <WithPermissionControl key="silence" userAction={UserAction.UpdateIncidents}>
      <ButtonCascader
        // @ts-ignore
        variant="secondary"
        className={className}
        disabled={disabled}
        onChange={onSelectCallback}
        options={silenceOptions.map((silenceOption: SelectOption) => ({
          value: silenceOption.value,
          label: silenceOption.display_name,
        }))}
        value={undefined}
        buttonProps={{ size: buttonSize as ComponentSize }}
      >
        Silence
      </ButtonCascader>
    </WithPermissionControl>
  );
});

export default SilenceDropdown;
