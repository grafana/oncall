import React, { useMemo } from 'react';

import { cx } from '@emotion/css';
import { useStyles2 } from '@grafana/ui';

import { getRotationFormStyles } from 'containers/RotationForm/RotationForm.styles';
import { SelectOption } from 'state/types';

interface DaysSelectorProps {
  value: string[];
  onChange: (value: string[]) => void;
  options: SelectOption[];
  weekStart: string;
  disabled?: boolean;
}

export const DaysSelector = ({ value, onChange, options: optionsProp, weekStart, disabled }: DaysSelectorProps) => {
  const getDayClickHandler = (day: string) => {
    return () => {
      const newValue = [...value];
      if (newValue.includes(day)) {
        const index = newValue.indexOf(day);
        newValue.splice(index, 1);
      } else {
        newValue.push(day);
      }
      onChange(newValue);
    };
  };

  const options = useMemo(() => {
    const index = optionsProp.findIndex(({ display_name }) => display_name.toLowerCase() === weekStart.toLowerCase());
    return [...optionsProp.slice(index), ...optionsProp.slice(0, index)];
  }, [optionsProp, weekStart]);

  const styles = useStyles2(getRotationFormStyles);

  return (
    <div className={cx(styles.days, { [styles.daysDisabled]: disabled })}>
      {options.map(({ display_name, value: itemValue }) => (
        <div
          key={display_name}
          onClick={getDayClickHandler(itemValue as string)}
          className={cx(styles.day, { [styles.daySelected]: value?.includes(itemValue as string) })}
        >
          {display_name.substring(0, 2)}
        </div>
      ))}
    </div>
  );
};
