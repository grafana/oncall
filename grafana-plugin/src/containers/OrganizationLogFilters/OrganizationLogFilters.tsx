import React, { ChangeEvent, useCallback, useMemo, useState } from 'react';

import { RawTimeRange } from '@grafana/data';
import { HorizontalGroup, Input, TimeRangeInput } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import RemoteSelect from 'containers/RemoteSelect/RemoteSelect';

import styles from './OrganizationLogFilters.module.css';

const cx = cn.bind(styles);

interface OrganizationLogFiltersProps {
  value: any;
  onChange: (filters: any) => void;
  className?: string;
}

const OrganizationLogFilters = observer((props: OrganizationLogFiltersProps) => {
  const { value, onChange } = props;

  const [createAtRaw, setCreateAtRaw] = useState<RawTimeRange>();

  const onSearchTermChangeCallback = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const filters = {
        ...value,
        search: e.currentTarget.value,
      };

      onChange(filters);
    },
    [onChange, value]
  );

  const getChangeHandler = (field: string) => {
    return (newValue: any) => {
      onChange({
        ...value,
        [field]: newValue,
      });
    };
  };

  const handleChangeCreatedAt = useCallback(
    (filter) => {
      onChange({
        ...value,
        created_at: filter.from._isValid && filter.to._isValid ? [filter.from, filter.to] : undefined,
      });

      setCreateAtRaw(filter.raw);
    },
    [value]
  );

  const createdAtValue = useMemo(() => {
    if (value['created_at']) {
      return { from: value['created_at'][0].toDate(), to: value['created_at'][1].toDate(), raw: createAtRaw };
    }
    return { from: undefined, to: undefined, raw: undefined };
  }, [value]);

  return (
    <div className={cx('root')}>
      <HorizontalGroup wrap>
        <Input
          className={cx('search')}
          placeholder="Search..."
          value={value['search']}
          onChange={onSearchTermChangeCallback}
        />
        <TimeRangeInput value={createdAtValue} onChange={handleChangeCreatedAt} hideTimeZone clearable />
        <RemoteSelect
          allowClear
          isMulti
          showSearch={false}
          className={cx('select')}
          value={value['labels']}
          onChange={getChangeHandler('labels')}
          href={'/organization_logs/label_options/'}
          fieldToShow="display_name"
          placeholder="Select labels..."
        />
      </HorizontalGroup>
    </div>
  );
});

export default OrganizationLogFilters;
