import React, { useCallback } from 'react';

import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { InlineSwitch, useStyles2 } from '@grafana/ui';

import { ApiSchemas } from 'network/oncall-api/api.types';

import { ScheduleFiltersType } from './ScheduleFilters.types';

interface SchedulesFiltersProps {
  value: ScheduleFiltersType;
  currentUserPk: ApiSchemas['User']['pk'];
  onChange: (filters: ScheduleFiltersType) => void;
}

export const ScheduleFilters = (props: SchedulesFiltersProps) => {
  const { value, currentUserPk, onChange } = props;
  const styles = useStyles2(getStyles);

  const handleShowMyShiftsOnlyClick = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const newUsers = [...value.users];

      if (event.target.checked && !value.users.includes(currentUserPk)) {
        newUsers.push(currentUserPk);
      } else {
        const index = value.users.findIndex((pk) => pk === currentUserPk);
        newUsers.splice(index, 1);
      }

      onChange({ ...value, users: newUsers });
    },
    [value]
  );

  return (
    <div className={styles.root}>
      <InlineSwitch
        showLabel
        label="Highlight my shifts"
        value={value.users.includes(currentUserPk)}
        onChange={handleShowMyShiftsOnlyClick}
      />
    </div>
  );
};

const getStyles = (_theme: GrafanaTheme2) => {
  return {
    root: css`
      display: block;
    `,
  };
};
