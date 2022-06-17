import React, { FC, useMemo, useState } from 'react';

import cn from 'classnames/bind';
import * as dayjs from 'dayjs';

import ScheduleSlot from 'components/ScheduleSlot/ScheduleSlot';
import Text from 'components/Text/Text';

import styles from './ScheduleTimeline.module.css';

const cx = cn.bind(styles);

interface ScheduleSlotState {}

interface ScheduleTimelineProps {
  layerIndex: number;
  rotationIndex: number;
}

const ScheduleTimeline: FC<ScheduleTimelineProps> = (props) => {
  const { layerIndex, rotationIndex, color, slots, label } = props;

  return (
    <div className={cx('root')}>
      {/* <div className={cx('current-time')} />*/}
      <div className={cx('slots')}>
        {slots.map(({ users, inactive }, slotIndex) => {
          return (
            <div className={cx('users')}>
              {users.map((user, userIndex) => (
                <ScheduleSlot
                  key={userIndex}
                  color={color}
                  label={slotIndex === 0 && userIndex === 0 && label}
                  user={user}
                  inactive={inactive}
                />
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ScheduleTimeline;
