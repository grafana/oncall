import React, { useMemo } from 'react';

import cn from 'classnames/bind';

import { SelectOption } from 'state/types';

import styles from 'containers/RotationForm/RotationForm.module.css';

const cx = cn.bind(styles);

interface DaysSelectorProps {
  value: string[];
  onChange: (value: string[]) => void;
  options: SelectOption[];
  weekStart: string;
}

const DaysSelector = ({ value, onChange, options: optionsProp, weekStart }: DaysSelectorProps) => {
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

  console.log(weekStart);

  const options = useMemo(() => {
    const index = optionsProp.findIndex(({ display_name }) => display_name.toLowerCase() === weekStart.toLowerCase());
    return [...optionsProp.slice(index), ...optionsProp.slice(0, index)];
  }, [optionsProp, weekStart]);

  return (
    <div className={cx('days')}>
      {options.map(({ display_name, value: itemValue }) => (
        <div
          key={display_name}
          onClick={getDayClickHandler(itemValue as string)}
          className={cx('day', { day__selected: value.includes(itemValue as string) })}
        >
          {display_name.substring(0, 2)}
        </div>
      ))}
    </div>
  );
};

export default DaysSelector;
