import React, { FC } from 'react';

import { SelectableValue } from '@grafana/data';
import { Select, ActionMeta } from '@grafana/ui';
import cn from 'classnames/bind';

import { NotificationPolicyValue } from 'containers/AddResponders/AddResponders.types';

import styles from './NotificationPoliciesSelect.module.scss';

const cx = cn.bind(styles);

type Props = {
  disabled?: boolean;
  important: boolean;
  onChange: (value: SelectableValue<number>, actionMeta: ActionMeta) => void;
};

const NotificationPoliciesSelect: FC<Props> = ({ disabled = false, important, onChange }) => (
  <Select
    className={cx('select')}
    width="auto"
    isSearchable={false}
    value={Number(important)}
    options={[
      {
        value: NotificationPolicyValue.Default,
        label: 'Default',
        description: 'Use "Default notifications" from users personal settings',
      },
      {
        value: NotificationPolicyValue.Important,
        label: 'Important',
        description: 'Use "Important notifications" from users personal settings',
      },
    ]}
    onChange={onChange}
    disabled={disabled}
  />
);

export default NotificationPoliciesSelect;
