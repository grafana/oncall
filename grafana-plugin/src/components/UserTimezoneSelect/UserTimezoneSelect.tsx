import React, { FC, useCallback, useMemo } from 'react';

import { Select } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { get } from 'lodash-es';

import { getTzOffsetString } from 'models/timezone/timezone.helpers';
import { Timezone } from 'models/timezone/timezone.types';
import { User } from 'models/user/user.types';

import styles from './UserTimezoneSelect.module.css';

interface UserTimezoneSelectProps {
  users: User[];
  value: Timezone;
  onChange: (value: Timezone) => void;
}

const cx = cn.bind(styles);

const UserTimezoneSelect: FC<UserTimezoneSelectProps> = (props) => {
  const { users, value, onChange } = props;

  const options = useMemo(() => {
    return users.reduce((memo, user) => {
      let item = memo.find((item) => item.label === user.tz);

      if (!item) {
        item = {
          value: user.pk,
          label: `${user.tz} ${getTzOffsetString(dayjs().tz(user.tz))}`,
          imgUrl: user.avatar,
          description: user.name,
        };
        memo.push(item);
      } else {
        item.description += ', ' + user.name;
        // item.imgUrl = undefined;
      }

      return memo;
    }, []);
  }, [users]);

  const selectValue = useMemo(() => {
    const user = users.find((user) => user.tz === value);
    return user.pk;
  }, [value, users]);

  const handleChange = useCallback(
    ({ value }) => {
      const user = users.find((user) => user.pk === value);

      onChange(user.tz);
    },
    [users]
  );

  return (
    <div className={cx('root')}>
      <Select value={selectValue} onChange={handleChange} width={100} placeholder="Timezone" options={options} />
    </div>
  );
};

export default UserTimezoneSelect;
