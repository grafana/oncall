import React, { useCallback } from 'react';

import { ButtonCascader, ComponentSize, Select } from '@grafana/ui';
import { observer } from 'mobx-react';

import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { SelectOption } from 'state/types';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization';

interface SilenceCascadingSelectProps {
  isCascading?: boolean;
  className?: string;
  disabled?: boolean;
  buttonSize?: string;

  onSelect: (value: number) => void;
}

const SilenceCascadingSelect = observer((props: SilenceCascadingSelectProps) => {
  const { onSelect, isCascading = true, className, disabled = false, buttonSize } = props;

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
      {isCascading ? renderAsCascader() : renderAsSelectDropdown()}
    </WithPermissionControl>
  );

  function renderAsCascader() {
    return (
      <ButtonCascader
        variant="secondary"
        className={className}
        disabled={disabled}
        onChange={onSelectCallback}
        options={getOptions()}
        value={undefined}
        buttonProps={{ size: buttonSize as ComponentSize }}
      >
        Silence
      </ButtonCascader>
    );
  }

  function renderAsSelectDropdown() {
    return (
      <Select
        menuShouldPortal
        className={''}
        placeholder="Silence for"
        onChange={onSelectCallback}
        options={getOptions()}
      />
    );
  }

  function getOptions() {
    return silenceOptions.map((silenceOption: SelectOption) => ({
      value: silenceOption.value,
      label: silenceOption.display_name,
    }));
  }
});

export default SilenceCascadingSelect;
