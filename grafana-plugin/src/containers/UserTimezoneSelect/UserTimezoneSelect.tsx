import React, { FC, useCallback, useEffect, useMemo, useState } from 'react';

import { SelectableValue } from '@grafana/data';
import { Select } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { sortBy } from 'lodash-es';
import { observer } from 'mobx-react';

import { allTimezones, getGMTTimezoneLabelBasedOnOffset, getTzOffsetString } from 'models/timezone/timezone.helpers';
import { UserHelper } from 'models/user/user.helpers';
import { useStore } from 'state/useStore';

import styles from './UserTimezoneSelect.module.css';

const cx = cn.bind(styles);

interface TimezoneOption {
  value: number; // utcOffset
  label: string;
  description: string;
}

interface UserTimezoneSelectProps {
  scheduleId?: string;
  onChange: (value: number) => void;
}

export const UserTimezoneSelect: FC<UserTimezoneSelectProps> = observer(({ scheduleId, onChange }) => {
  const store = useStore();
  const users = UserHelper.getSearchResult(store.userStore).results || [];

  const [extraOptions, setExtraOptions] = useState<TimezoneOption[]>([
    {
      value: 0,
      label: 'GMT',
      description: '',
    },
  ]);

  const options = useMemo(() => {
    return sortBy(
      users.reduce(
        (memo, user) => {
          const moment = dayjs().tz(user.timezone);
          const utcOffset = moment.utcOffset();

          let item = memo.find((item) => item.value === utcOffset);

          if (!item) {
            item = {
              value: utcOffset,
              label: getGMTTimezoneLabelBasedOnOffset(utcOffset),
              description: user.username,
            };

            memo.push(item);
          } else {
            item.description += item.description ? ', ' + user.username : user.username;
          }

          return memo;
        },
        [...extraOptions.map((option) => ({ ...option }))]
      ),
      ({ value }) => value
    );
  }, [users, extraOptions]);

  const selectedOption = options.find(({ value }) => value === store.timezoneStore.selectedTimezoneOffset);

  const filterOption = useCallback((item: SelectableValue<number>, searchQuery: string) => {
    const { data } = item;

    return ['label', 'description', 'timezone'].some((key: string) => {
      if (data.__isNew_) {
        return true;
      }
      return data[key]?.toLowerCase().includes(searchQuery.toLowerCase());
    });
  }, []);

  useEffect(() => {
    if (selectedOption?.value) {
      store.timezoneStore.setSelectedTimezoneOffset(selectedOption.value);
    }
  }, [options]);

  const handleCreateOption = useCallback(
    (value: string) => {
      const matched = allTimezones.find((tz) => tz.toLowerCase().includes(value.toLowerCase()));
      if (matched) {
        const now = dayjs().tz(matched);
        const utcOffset = now.utcOffset();
        store.timezoneStore.setSelectedTimezoneOffset(utcOffset);
        store.scheduleStore.refreshEvents(scheduleId);

        if (options.some((option) => option.value === utcOffset)) {
          return;
        }

        setExtraOptions((extraOptions) => [
          ...extraOptions,
          {
            value: utcOffset,
            timezone: matched,
            label: getTzOffsetString(now),
            description: '',
          },
        ]);
      }
    },
    [options]
  );

  return (
    <div className={cx('root')} data-testid="timezone-select">
      <Select
        value={selectedOption}
        onChange={(option) => {
          store.timezoneStore.setSelectedTimezoneOffset(option.value);

          onChange(option.value);
        }}
        width={30}
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
});
