import React, { FC } from 'react';

import { css } from '@emotion/css';
import { SelectableValue } from '@grafana/data';
import { Select, ActionMeta } from '@grafana/ui';

import { NotificationPolicyValue } from 'containers/AddResponders/AddResponders.types';

type Props = {
  disabled?: boolean;
  important: boolean;
  onChange: (value: SelectableValue<number>, actionMeta: ActionMeta) => void;
};

export const NotificationPoliciesSelect: FC<Props> = ({ disabled = false, important, onChange }) => (
  <Select
    className={css`
      width: 150px !important;
    `}
    width="auto"
    isSearchable={false}
    value={Number(important)}
    options={[
      {
        value: NotificationPolicyValue.Default,
        label: 'Default',
        description: 'Use "Default notification rules" from users personal settings',
      },
      {
        value: NotificationPolicyValue.Important,
        label: 'Important',
        description: 'Use "Important notification rules" from users personal settings',
      },
    ]}
    onChange={onChange}
    disabled={disabled}
  />
);
