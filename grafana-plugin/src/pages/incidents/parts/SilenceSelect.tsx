import React from 'react';

import { Select } from '@grafana/ui';
import { observer } from 'mobx-react';

import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { SelectOption } from 'state/types';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization';

interface SilenceSelectProps {
  placeholder?: string;

  onSelect: (value: number) => void;
}

export const SilenceSelect = observer((props: SilenceSelectProps) => {
  const { placeholder = 'Silence for', onSelect } = props;

  const store = useStore();

  const { alertGroupStore } = store;

  const silenceOptions = alertGroupStore.silenceOptions || [];

  return (
    <WithPermissionControlTooltip key="silence" userAction={UserActions.AlertGroupsWrite}>
      <Select
        menuShouldPortal
        placeholder={placeholder}
        value={undefined}
        onChange={({ value }) => onSelect(Number(value))}
        options={getOptions()}
      />
    </WithPermissionControlTooltip>
  );

  function getOptions() {
    return silenceOptions.map((silenceOption: SelectOption) => ({
      value: silenceOption.value,
      label: silenceOption.display_name,
    }));
  }
});
