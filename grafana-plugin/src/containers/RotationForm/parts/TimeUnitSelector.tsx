import React, { useMemo } from 'react';

import { Select } from '@grafana/ui';
import cn from 'classnames/bind';

import { repeatEveryPeriodToUnitName } from 'containers/RotationForm/RotationForm.helpers';
import { RepeatEveryPeriod } from 'containers/RotationForm/RotationForm.types';

import styles from 'containers/RotationForm/RotationForm.module.css';

const cx = cn.bind(styles);

interface TimeUnitSelectorProps {
  value: number;
  unit: RepeatEveryPeriod;
  maxValue: number;
  onChange: (value) => void;
  className?: string;
  disabled?: boolean;
}

const TimeUnitSelector = ({ value, unit, onChange, maxValue, className, disabled }: TimeUnitSelectorProps) => {
  const handleChange = ({ value }) => {
    onChange(value);
  };

  const options = useMemo(
    () =>
      Array.from(Array(maxValue + 1).keys()).map((i) => ({
        label: `${String(i)} ${
          i === 1 ? repeatEveryPeriodToUnitName[unit].slice(0, -1) : repeatEveryPeriodToUnitName[unit]
        }`,
        value: i,
      })),
    [maxValue]
  );

  return (
    <div className={cx('root', className)}>
      <Select disabled={disabled} value={value} options={options} onChange={handleChange} />
    </div>
  );
};

export default TimeUnitSelector;
