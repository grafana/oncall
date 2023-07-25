import React, { FC, useCallback, useMemo, useState } from 'react';

import { SelectableValue } from '@grafana/data';
import { Select } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';

import { getTzOffsetString, allTimezones } from 'models/timezone/timezone.helpers';
import { Timezone } from 'models/timezone/timezone.types';
import { User } from 'models/user/user.types';

import styles from './UserTimezoneSelect.module.css';

interface UserTimezoneSelectProps {
  users: User[];
  value: Timezone;
  onChange: (value: Timezone) => void;
}

const cx = cn.bind(styles);

interface TimezoneOption {
  value: number;
  utcOffset: number;
  timezone: Timezone;
  label: string;
  description: string;
}

const UserTimezoneSelect: FC<UserTimezoneSelectProps> = (props) => {
  const { users, value: propValue, onChange } = props;

  const [extraOptions, setExtraOptions] = useState<TimezoneOption[]>([
    {
      value: 0,
      utcOffset: 0,
      timezone: 'UTC' as Timezone,
      label: 'GMT',
      description: '',
    },
  ]);

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
        [...extraOptions.map((option) => ({ ...option }))]
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
  }, [users, extraOptions]);

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

  const filterOption = useCallback((item: SelectableValue<number>, searchQuery: string) => {
    const { data } = item;

    return ['label', 'description', 'timezone'].some((key: string) => {
      if (data.__isNew_) {
        return true;
      }
      return data[key] && data[key].toLowerCase().includes(searchQuery.toLowerCase());
    });
  }, []);

  const handleCreateOption = useCallback(
    (value: string) => {
      const matched = allTimezones.find((tz) => tz.toLowerCase().includes(value.toLowerCase()));
      if (matched) {
        const now = dayjs().tz(matched);
        const utcOffset = now.utcOffset();
        onChange(matched);

        if (options.some((option) => option.utcOffset === utcOffset)) {
          return;
        }

        setExtraOptions((extraOptions) => [
          ...extraOptions,
          {
            value: utcOffset,
            utcOffset,
            timezone: matched,
            label: getTzOffsetString(now),
            description: '',
          },
        ]);

        onChange(matched);
      }
    },
    [options]
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
        allowCustomValue
        onCreateOption={handleCreateOption}
        formatCreateLabel={(input: string) => {
          const matched = allTimezones.find((tz) => tz.toLowerCase().includes(input.toLowerCase()));
          const now = dayjs().tz(matched);
          if (matched) {
            return `Select ${getTzOffsetString(now)} (${matched})`;
          } else {
            return `Not found`;
          }
        }}
      />
    </div>
  );
};

export default UserTimezoneSelect;
