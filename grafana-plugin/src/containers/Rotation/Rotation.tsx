import React, { FC, useMemo, useState, useEffect } from 'react';

import { LoadingPlaceholder } from '@grafana/ui';
import cn from 'classnames/bind';
import * as dayjs from 'dayjs';
import { observer } from 'mobx-react';

import ScheduleSlot from 'components/ScheduleSlot/ScheduleSlot';
import Text from 'components/Text/Text';
import { Rotation as RotationType } from 'models/schedule/schedule.types';
import { useStore } from 'state/useStore';

import styles from './Rotation.module.css';

const cx = cn.bind(styles);

interface ScheduleSlotState {}

interface RotationProps {
  id: RotationType['id'];
  layerIndex: number;
  rotationIndex: number;
  label: string;
}

const Rotation: FC<RotationProps> = observer((props) => {
  const { id, layerIndex, rotationIndex, label } = props;

  const store = useStore();

  useEffect(() => {
    store.scheduleStore.updateRotation(id);
  }, []);

  const rotation = store.scheduleStore.rotations[id];

  if (!rotation) {
    return <LoadingPlaceholder text="Loading shifts..." />;
  }

  const { shifts } = rotation;

  return (
    <div className={cx('root')}>
      {/* <div className={cx('current-time')} />*/}
      <div className={cx('timeline')}>
        <div className={cx('slots')}>
          {shifts.map((shift, index) => {
            return (
              <ScheduleSlot
                key={index}
                index={index}
                shift={shift}
                layerIndex={layerIndex}
                rotationIndex={rotationIndex}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
});

export default Rotation;
