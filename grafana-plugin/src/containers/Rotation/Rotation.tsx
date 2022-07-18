import React, { FC, useMemo, useState, useEffect } from 'react';

import { LoadingPlaceholder } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';

import ScheduleSlot from 'components/ScheduleSlot/ScheduleSlot';
import Text from 'components/Text/Text';
import { Rotation as RotationType } from 'models/schedule/schedule.types';
import { Timezone } from 'models/timezone/timezone.types';
import { useStore } from 'state/useStore';

import styles from './Rotation.module.css';

const cx = cn.bind(styles);

interface ScheduleSlotState {}

interface RotationProps {
  id: RotationType['id'];
  layerIndex: number;
  rotationIndex: number;
  label: string;
  startMoment: dayjs.Dayjs;
  currentTimezone: Timezone;
}

const Rotation: FC<RotationProps> = observer((props) => {
  const { id, layerIndex, rotationIndex, label, startMoment, currentTimezone } = props;

  const store = useStore();

  useEffect(() => {
    store.scheduleStore.updateRotation(id);
  }, []);

  const rotation = store.scheduleStore.rotations[id];

  if (!rotation) {
    return <LoadingPlaceholder text="Loading shifts..." />;
  }

  const base = 60 * 24 * 7; // in minutes
  const utcOffset = dayjs().tz(currentTimezone).utcOffset();

  const x = utcOffset / base;

  const { shifts } = rotation;

  return (
    <div className={cx('root')}>
      {/* <div className={cx('current-time')} />*/}
      <div className={cx('timeline')}>
        <div className={cx('slots')} style={{ transform: `translate(${x * 100}%, 0)` }}>
          {shifts.map((shift, index) => {
            return (
              <ScheduleSlot
                key={index}
                index={index}
                shift={shift}
                layerIndex={layerIndex}
                rotationIndex={rotationIndex}
                startMoment={startMoment}
                currentTimezone={currentTimezone}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
});

export default Rotation;
