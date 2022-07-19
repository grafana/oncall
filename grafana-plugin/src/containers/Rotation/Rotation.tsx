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
  label: string;
  startMoment: dayjs.Dayjs;
  currentTimezone: Timezone;
  layerIndex?: number;
  rotationIndex?: number;
  color?: string;
}

const Rotation: FC<RotationProps> = observer((props) => {
  const { id, layerIndex, rotationIndex, label, startMoment, currentTimezone, color } = props;

  const store = useStore();

  useEffect(() => {
    const startMomentString = startMoment.utc().format('YYYY-MM-DDTHH:mm:ss.000Z');

    store.scheduleStore.updateRotationMock(id, startMomentString);
  }, [startMoment]);

  const rotation = store.scheduleStore.rotations[id];

  if (!rotation) {
    return (
      <div className={cx('root')}>
        <LoadingPlaceholder text="Loading shifts..." />
      </div>
    );
  }

  const { shifts } = rotation;

  const firstShift = shifts[0];

  const firstShiftOffset = firstShift.start.diff(startMoment, 'minutes');

  const base = 60 * 24 * 7; // in minutes only
  const utcOffset = dayjs().tz(currentTimezone).utcOffset();

  const x = (firstShiftOffset + utcOffset) / base;

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
                color={color}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
});

export default Rotation;
