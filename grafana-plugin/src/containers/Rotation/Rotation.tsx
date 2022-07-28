import React, { FC, useMemo, useState, useEffect, useRef, useCallback } from 'react';

import { HorizontalGroup, LoadingPlaceholder } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';
import { CSSTransitionGroup } from 'react-transition-group'; // ES6

import ScheduleSlot from 'components/ScheduleSlot/ScheduleSlot';
import Text from 'components/Text/Text';
import { getFromString } from 'models/schedule/schedule.helpers';
import { Rotation as RotationType, Schedule, Event } from 'models/schedule/schedule.types';
import { Timezone } from 'models/timezone/timezone.types';
import { useStore } from 'state/useStore';
import { usePrevious } from 'utils/hooks';

import styles from './Rotation.module.css';

const cx = cn.bind(styles);

interface ScheduleSlotState {}

interface RotationProps {
  startMoment: dayjs.Dayjs;
  currentTimezone: Timezone;
  layerIndex?: number;
  rotationIndex?: number;
  color?: string;
  events: Event[];
}

const Rotation: FC<RotationProps> = observer((props) => {
  const { events, layerIndex, rotationIndex, startMoment, currentTimezone, color } = props;

  const [animate, setAnimate] = useState<boolean>(true);
  const [width, setWidth] = useState<number | undefined>();
  const [transparent, setTransparent] = useState<boolean>(false);

  const store = useStore();

  const startMomentString = useMemo(() => getFromString(startMoment), [startMoment]);

  const prevStartMomentString = usePrevious(startMomentString);

  // console.log(events);

  // const rotation = store.scheduleStore.rotations[id]?.[prevStartMomentString];

  /* useEffect(() => {
    setTransparent(false);
  }, [rotation]);

  useEffect(() => {
    setTransparent(true);
  }, [startMoment]);*/

  useEffect(() => {
    const startMomentString = startMoment.utc().format('YYYY-MM-DDTHH:mm:ss.000Z');

    // console.log('CHANGE START MOMENT', startMomentString);

    // store.scheduleStore.updateEvents(scheduleId, startMomentString, currentTimezone);
  }, [startMomentString]);

  const slots = useCallback((node) => {
    if (node) {
      setWidth(node.offsetWidth);
    }
  }, []);

  const x = useMemo(() => {
    if (!events || !events.length) {
      return 0;
    }

    const firstShift = events[0];

    const firstShiftOffset = dayjs(firstShift.start).diff(startMoment, 'seconds');

    const base = 60 * 60 * 24 * 7; // in minutes only
    // const utcOffset = dayjs().tz(currentTimezone).utcOffset();

    return firstShiftOffset / base;
  }, [events]);

  return (
    <div className={cx('root')}>
      {/* <div className={cx('current-time')} />*/}
      <div className={cx('timeline')}>
        {events ? (
          events.length ? (
            <div
              className={cx('slots', { slots__animate: animate, slots__transparent: transparent })}
              style={{ transform: `translate(${x * 100}%, 0)` }}
              ref={slots}
            >
              {events.map((event, index) => {
                return (
                  <ScheduleSlot
                    index={index}
                    key={event.start}
                    event={event}
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
            <div className={cx('empty')} />
          )
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
