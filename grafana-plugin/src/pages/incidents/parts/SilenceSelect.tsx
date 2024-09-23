import React from 'react';

import { Select } from '@grafana/ui';
import { UserActions } from 'helpers/authorization/authorization';
import { observer } from 'mobx-react';

import { SILENCE_DURATION_LIST } from 'components/Policy/Policy.consts';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';

interface SilenceSelectProps {
  placeholder?: string;
  disabled?: boolean;

  onSelect: (value: number) => void;
}

export const SilenceSelect = observer((props: SilenceSelectProps) => {
  const { placeholder = 'Silence for', disabled = false, onSelect } = props;

  return (
    <>
      {' '}
      <WithPermissionControlTooltip key="silence" userAction={UserActions.AlertGroupsWrite}>
        <Select
          disabled={disabled}
          menuShouldPortal
          placeholder={placeholder}
          value={undefined}
          onChange={({ value }) => {
            onSelect(Number(value));
          }}
          options={getOptions()}
        />
      </WithPermissionControlTooltip>
    </>
  );

  function getOptions() {
    return [...SILENCE_DURATION_LIST];
  }
});
