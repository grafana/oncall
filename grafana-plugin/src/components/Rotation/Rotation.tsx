import React, { FC } from 'react';

import cn from 'classnames/bind';

import ScheduleTimeline from 'components/ScheduleTimeline/ScheduleTimeline';

import styles from './Rotation.module.css';

interface RotationProps {}

const cx = cn.bind(styles);

const Rotation: FC<RotationProps> = (props) => {
  const { layerIndex, rotationIndex, slots, color, label } = props;

  return (
    <div className={cx('root')}>
      <div className={cx('timeline')}>
        <ScheduleTimeline
          layerIndex={layerIndex}
          rotationIndex={rotationIndex}
          slots={slots}
          color={color}
          label={label}
        />
      </div>
    </div>
  );
};

export default Rotation;
