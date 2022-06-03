import React, { useCallback, useEffect } from 'react';

import { IconButton, ValuePicker, WithContextMenu, ButtonCascader } from '@grafana/ui';
import { observer } from 'mobx-react';

import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { SelectOption } from 'state/types';
import { useStore } from 'state/useStore';
import { UserAction } from 'state/userAction';

interface SilenceDropdownProps {
  onSelect: (value: number) => void;
  className?: string;
  disabled?: boolean;
}

const SilenceDropdown = observer((props: SilenceDropdownProps) => {
  const { onSelect, className, disabled = false } = props;

  const onSelectCallback = useCallback(
    ([value, ...rest]) => {
      onSelect(Number(value));
    },
    [onSelect]
  );

  const store = useStore();

  const { alertGroupStore } = store;

  const silenceOptions = alertGroupStore.silenceOptions || [];

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
      >
        Silence
      </ButtonCascader>
    </WithPermissionControl>
  );
});

export default SilenceDropdown;
