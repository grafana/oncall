import React from 'react';

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
        onChange={(value) => onSelect(Number(value))}
        options={getOptions()}
        value={undefined}
        buttonProps={{ size: buttonSize as ComponentSize }}
      >
        Silence
      </ButtonCascader>
    );
  }

  function renderAsSelectDropdown() {
    console.log('render');
    return (
      <Select
        menuShouldPortal
        placeholder="Silence for"
        value={undefined}
        onChange={({ value }) => onSelect(Number(value))}
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
