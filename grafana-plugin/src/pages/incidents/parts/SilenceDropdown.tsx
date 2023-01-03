import React, { useCallback } from 'react';

import { ButtonCascader, ComponentSize } from '@grafana/ui';
import { observer } from 'mobx-react';

import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { SelectOption } from 'state/types';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization';

interface SilenceDropdownProps {
  onSelect: (value: number) => void;
  className?: string;
  disabled?: boolean;
  buttonSize?: string;
}

const SilenceDropdown = observer((props: SilenceDropdownProps) => {
  const { onSelect, className, disabled = false, buttonSize } = props;

  const onSelectCallback = useCallback(
    ([value]) => {
      onSelect(Number(value));
    },
    [onSelect]
  );

  const store = useStore();

  const { alertGroupStore } = store;

  const silenceOptions = alertGroupStore.silenceOptions || [];

  return (
    <WithPermissionControl key="silence" userAction={UserActions.AlertGroupsWrite}>
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
