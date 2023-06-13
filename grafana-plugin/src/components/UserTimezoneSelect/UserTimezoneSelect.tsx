import React, { FC, useCallback, useMemo } from 'react';

import { SelectableValue } from '@grafana/data';
import { Select } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';

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
  const { users, value: propValue, onChange } = props;

  const options = useMemo(() => {
    return users
      .reduce(
        (memo, user) => {
          const moment = dayjs().tz(user.timezone);
          const utcOffset = moment.utcOffset();

          let item = memo.find((item) => item.utcOffset === utcOffset);

          if (!item) {
            item = {
              value: utcOffset,
              utcOffset,
              timezone: user.timezone,
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
            value: 0,
            utcOffset: 0,
            timezone: 'UTC' as Timezone,
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

  const value = useMemo(() => {
    const utcOffset = dayjs().tz(propValue).utcOffset();
    const option = options.find((option) => option.utcOffset === utcOffset);

    return option?.value;
  }, [propValue, options]);

  const handleChange = useCallback(
    ({ value }) => {
      const option = options.find((option) => option.utcOffset === value);
      onChange(option?.timezone);
    },
    [options]
  );

  const filterOption = useCallback(
    ({ data }: SelectableValue<number>, searchQuery: string) =>
      ['label', 'description', 'timezone'].some((key: string) =>
        data[key].toLowerCase().includes(searchQuery.toLowerCase())
      ),
    []
  );

  return (
    <div className={cx('root')}>
      <Select
        value={value}
        onChange={handleChange}
        width={30}
        placeholder={propValue}
        options={options}
        filterOption={filterOption}
      />
    </div>
  );
};

export default UserTimezoneSelect;
