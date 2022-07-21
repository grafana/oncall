import React, { FC, useMemo, useState, useEffect, useRef, useCallback } from 'react';

import { HorizontalGroup, LoadingPlaceholder } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';
import { CSSTransitionGroup } from 'react-transition-group'; // ES6

import ScheduleSlot from 'components/ScheduleSlot/ScheduleSlot';
import Text from 'components/Text/Text';
import { Rotation as RotationType } from 'models/schedule/schedule.types';
import { Timezone } from 'models/timezone/timezone.types';
import { useStore } from 'state/useStore';
import { usePrevious } from 'utils/hooks';

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

  const [animate, setAnimate] = useState<boolean>(true);
  const [width, setWidth] = useState<number | undefined>();
  const [transparent, setTransparent] = useState<boolean>(false);

  const store = useStore();

  const startMomentString = useMemo(() => startMoment.utc().format('YYYY-MM-DDTHH:mm:ss.000Z'), [startMoment]);

  const prevStartMomentString = usePrevious(startMomentString);

  const rotation = store.scheduleStore.rotations[id]?.[startMomentString];
  //const rotation = store.scheduleStore.rotations[id]?.[prevStartMomentString];

  /* useEffect(() => {
    setTransparent(false);
  }, [rotation]);

  useEffect(() => {
    setTransparent(true);
  }, [startMoment]);*/

  useEffect(() => {
    const startMomentString = startMoment.utc().format('YYYY-MM-DDTHH:mm:ss.000Z');

    console.log('CHANGE START MOMENT', startMomentString);

    store.scheduleStore.updateRotationMock(id, startMomentString, currentTimezone);
  }, [startMomentString]);

  const slots = useCallback((node) => {
    if (node) {
      setWidth(node.offsetWidth);
    }
  }, []);

  const x = useMemo(() => {
    if (!rotation) {
      return 0;
    }

    const { shifts } = rotation;

    const firstShift = shifts[0];

    const firstShiftOffset = firstShift.start.diff(startMoment, 'minutes');

    const base = 60 * 24 * 7; // in minutes only
    const utcOffset = dayjs().tz(currentTimezone).utcOffset();

    return firstShiftOffset / base;
  }, [rotation]);

  useEffect(() => {});

  return (
    <div className={cx('root')}>
      {/* <div className={cx('current-time')} />*/}
      <div className={cx('timeline')}>
        {rotation ? (
          <div
            className={cx('slots', { slots__animate: animate, slots__transparent: transparent })}
            style={{ transform: `translate(${x * 100}%, 0)` }}
            ref={slots}
          >
            {rotation.shifts.map((shift, index) => {
              return (
                <ScheduleSlot
                  key={shift.pk}
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
        ) : (
          <HorizontalGroup align="center" justify="center">
            <LoadingPlaceholder text="Loading shifts..." />
          </HorizontalGroup>
        )}
      </div>
    </div>
  );
});

export default Rotation;
