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
    return users
      .reduce(
        (memo, user) => {
          const moment = dayjs().tz(user.timezone);
          const utcOffset = moment.utcOffset();

          let item = memo.find((item) => item.utcOffset === utcOffset);

          if (!item) {
            item = {
              value: user.timezone,
              utcOffset,
              label: getTzOffsetString(moment),
              description: user.username,
            };
            memo.push(item);
          } else {
            item.description += item.description ? ', ' + user.username : user.username;
            // item.imgUrl = undefined;
          }

          return memo;
        },
        [
          {
            value: 'UTC',
            utcOffset: 0,
            label: 'GMT',
            description: '',
          },
        ]
      )
      .sort((a, b) => {
        if (b.utcOffset === 0) {
          return 1;
        }

        if (a.utcOffset > b.utcOffset) {
          return 1;
        }
        if (a.utcOffset < b.utcOffset) {
          return -1;
        }

        return 0;
      });
  }, [users]);

  const handleChange = useCallback(
    ({ value }) => {
      const option = options.find((option) => option.timezone === value);

      onChange(value);
    },
    [users]
  );

  return (
    <div className={cx('root')}>
      <Select value={value} onChange={handleChange} width={100} placeholder="UTC Timezone" options={options} />
    </div>
  );
};

export default UserTimezoneSelect;
