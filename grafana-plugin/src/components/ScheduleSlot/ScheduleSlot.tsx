import React, { FC, useCallback, useState } from 'react';

import { HorizontalGroup, Icon, Tooltip, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';

import Line from 'components/ScheduleUserDetails/img/line.svg';
import Text from 'components/Text/Text';
import WorkingHours from 'components/WorkingHours/WorkingHours';
import { Event } from 'models/schedule/schedule.types';
import { Timezone } from 'models/timezone/timezone.types';
import { User } from 'models/user/user.types';
import { useStore } from 'state/useStore';

import { getColor, getLabel, getTitle } from './ScheduleSlot.helpers';

import styles from './ScheduleSlot.module.css';

interface ScheduleSlotProps {
  index: number;
  layerIndex: number;
  rotationIndex: number;
  event: Event;
  startMoment: dayjs.Dayjs;
  currentTimezone: Timezone;
  color?: string;
}

const cx = cn.bind(styles);

const ScheduleSlot: FC<ScheduleSlotProps> = observer((props) => {
  const { index, layerIndex, rotationIndex, event, startMoment, currentTimezone, color: propColor } = props;
  const { users } = event;

  const trackMouse = true;

  const [mouseX, setMouseX] = useState<number>(0);

  const start = dayjs(event.start);
  const end = dayjs(event.end);

  const duration = end.diff(start, 'seconds');

  const store = useStore();

  const base = 60 * 60 * 24 * 7;

  const width = duration / base;

  const label = !isNaN(layerIndex) && !isNaN(rotationIndex) && index === 0 ? getLabel(layerIndex, rotationIndex) : null;

  const handleMouseMove = useCallback((event) => {
    setMouseX(event.nativeEvent.offsetX);
  }, []);

  return (
    <div className={cx('stack')} style={{ width: `${width * 100}%` /*left: `${x * 100}%`*/ }}>
      {!event.is_gap ? (
        users.map(({ pk: userPk }, userIndex) => {
          const storeUser = store.userStore.items[userPk];

          const inactive = false;

          const color = propColor || getColor(layerIndex, rotationIndex);
          const title = getTitle(storeUser);

          return (
            <Tooltip content={<ScheduleSlotDetails user={storeUser} currentTimezone={currentTimezone} event={event} />}>
              <div
                className={cx('root', { root__inactive: inactive })}
                style={{
                  backgroundColor: color,
                }}
                onMouseMove={trackMouse ? handleMouseMove : undefined}
                onMouseLeave={trackMouse ? () => setMouseX(0) : undefined}
              >
                {trackMouse && mouseX > 0 && <div style={{ left: `${mouseX}px` }} className={cx('time')} />}
                {storeUser && (
                  <WorkingHours
                    className={cx('working-hours')}
                    timezone={storeUser.timezone}
                    workingHours={storeUser.working_hours}
                    startMoment={start}
                    duration={duration}
                  />
                )}
                {userIndex === 0 && label && (
                  <div className={cx('label')} style={{ color }}>
                    {label}
                  </div>
                )}
                <div className={cx('title')}>{title}</div>
              </div>
            </Tooltip>
          );
        })
      ) : (
        <Tooltip content={<ScheduleGapDetails event={event} currentTimezone={currentTimezone} />}>
          <div className={cx('root', 'root__type_gap')} style={{}}>
            {trackMouse && mouseX > 0 && <div style={{ left: `${mouseX}px` }} className={cx('time')} />}
            {label && <div className={cx('label')}>{label}</div>}
          </div>
        </Tooltip>
      )}
    </div>
  );
});

export default ScheduleSlot;

interface ScheduleSlotDetailsProps {
  user: User;
  currentTimezone: Timezone;
  event: Event;
}

const ScheduleSlotDetails = (props: ScheduleSlotDetailsProps) => {
  const { user, currentTimezone, event } = props;

  const userStatus = 'success';

  return (
    <div className={cx('details')}>
      <HorizontalGroup>
        <VerticalGroup spacing="sm">
          <HorizontalGroup spacing="md">
            <div
              className={cx('details-user-status', {
                [`details-user-status__type_${userStatus}`]: true,
              })}
            />
            <Text type="secondary">{user?.username}</Text>
          </HorizontalGroup>
          <HorizontalGroup>
            <VerticalGroup spacing="none">
              {/* <HorizontalGroup spacing="sm">
                <Icon name="clock-nine" size="xs" />
                <Text type="secondary">30 apr, 7:54 </Text>
              </HorizontalGroup>*/}
              <HorizontalGroup spacing="sm">
                <img src={Line} />
                <VerticalGroup spacing="none">
                  <Text type="secondary">{dayjs(event.start).tz(user.timezone).format('DD MMM, HH:mm')}</Text>
                  <Text type="secondary">{dayjs(event.end).tz(user.timezone).format('DD MMM, HH:mm')}</Text>
                </VerticalGroup>
              </HorizontalGroup>
            </VerticalGroup>
          </HorizontalGroup>
        </VerticalGroup>
        <VerticalGroup spacing="sm">
          <Text type="primary">{currentTimezone}</Text>
          <VerticalGroup spacing="none">
            {/* <Text type="primary">30 apr, 12:54 </Text>*/}
            <Text type="primary">{dayjs(event.start).tz(currentTimezone).format('DD MMM, HH:mm')}</Text>
            <Text type="primary">{dayjs(event.end).tz(currentTimezone).format('DD MMM, HH:mm')}</Text>
          </VerticalGroup>
        </VerticalGroup>
      </HorizontalGroup>
    </div>
  );
};

interface ScheduleGapDetailsProps {
  currentTimezone: Timezone;
  event: Event;
}

const ScheduleGapDetails = (props: ScheduleGapDetailsProps) => {
  const { currentTimezone, event } = props;

  return (
    <div className={cx('details')}>
      <VerticalGroup>
        <HorizontalGroup spacing="sm">
          <VerticalGroup spacing="none">
            <Text type="primary">{currentTimezone}</Text>
            <Text type="primary">{dayjs(event.start).tz(currentTimezone).format('DD MMM, HH:mm')}</Text>
            <Text type="primary">{dayjs(event.end).tz(currentTimezone).format('DD MMM, HH:mm')}</Text>
          </VerticalGroup>
        </HorizontalGroup>
        {/*<Text type="primary">Gaps this week</Text>
        <HorizontalGroup justify="space-between">
          <Text type="secondary">Number of gaps</Text>
          <Text type="secondary">12</Text>
        </HorizontalGroup>
        <HorizontalGroup justify="space-between">
          <Text type="secondary">Time</Text>
          <Text type="secondary">23h 12m</Text>
        </HorizontalGroup>*/}
      </VerticalGroup>
    </div>
  );
};
