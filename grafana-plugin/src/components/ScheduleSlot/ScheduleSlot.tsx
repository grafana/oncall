import React, { FC } from 'react';

import { HorizontalGroup, Icon, Tooltip, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';

import Line from 'components/ScheduleUserDetails/img/line.svg';
import Text from 'components/Text/Text';
import WorkingHours from 'components/WorkingHours/WorkingHours';
import { Shift } from 'models/schedule/schedule.types';
import { Timezone } from 'models/timezone/timezone.types';
import { User } from 'models/user/user.types';
import { useStore } from 'state/useStore';

import { getColor, getLabel, getTitle } from './ScheduleSlot.helpers';

import styles from './ScheduleSlot.module.css';

interface ScheduleSlotProps {
  index: number;
  layerIndex: number;
  rotationIndex: number;
  shift: Shift;
  startMoment: dayjs.Dayjs;
  currentTimezone: Timezone;
  color?: string;
}

const cx = cn.bind(styles);

const ScheduleSlot: FC<ScheduleSlotProps> = observer((props) => {
  const { index, layerIndex, rotationIndex, shift, startMoment, currentTimezone, color: propColor } = props;
  const { duration, users } = shift;

  const isGap = !users.length;

  const store = useStore();

  const base = 60 * 60 * 24 * 7;

  const width = duration / base;

  return (
    <div className={cx('stack')} style={{ width: `${width * 100}%` /*left: `${x * 100}%`*/ }}>
      {!isGap ? (
        users.map((pk, userIndex) => {
          const label =
            !isNaN(layerIndex) && !isNaN(rotationIndex) && index === 0 && userIndex === 0
              ? getLabel(layerIndex, rotationIndex)
              : null;
          const storeUser = store.userStore.items[pk];

          const inactive = false;

          const color = propColor || getColor(layerIndex, rotationIndex);
          const title = getTitle(storeUser);

          return (
            <Tooltip content={<ScheduleSlotDetails user={storeUser} currentUser={store.userStore.currentUser} />}>
              <div
                className={cx('root', { root__inactive: inactive })}
                style={{
                  backgroundColor: color,
                }}
              >
                {storeUser && (
                  <WorkingHours
                    className={cx('working-hours')}
                    // timezone={storeUser.timezone}
                    timezone={['America/Vancouver', 'Europe/London'][userIndex]}
                    //workingHours={storeUser.working_hours}
                    startMoment={shift.start}
                    duration={shift.duration}
                  />
                )}
                {label && (
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
        <Tooltip content={<ScheduleGapDetails />}>
          <div className={cx('root', 'root__type_gap')} style={{}}>
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
  currentUser: User;
}

const ScheduleSlotDetails = (props: ScheduleSlotDetailsProps) => {
  const { user, currentUser } = props;

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
              <HorizontalGroup spacing="sm">
                <Icon name="clock-nine" size="xs" />
                <Text type="secondary">30 apr, 7:54 </Text>
              </HorizontalGroup>
              <HorizontalGroup spacing="sm">
                <img src={Line} />
                <VerticalGroup spacing="none">
                  <Text type="secondary">30 apr, 00:00</Text>
                  <Text type="secondary">30 apr, 23:59</Text>
                </VerticalGroup>
              </HorizontalGroup>
            </VerticalGroup>
          </HorizontalGroup>
        </VerticalGroup>
        <VerticalGroup spacing="sm">
          <Text type="primary">{currentUser?.username}</Text>
          <VerticalGroup spacing="none">
            <Text type="primary">30 apr, 12:54 </Text>
            <Text type="primary">29 apr, 20:00 </Text>
            <Text type="primary">30 apr, 20:00 </Text>
          </VerticalGroup>
        </VerticalGroup>
      </HorizontalGroup>
    </div>
  );
};

interface ScheduleGapDetailsProps {}

const ScheduleGapDetails = (props: ScheduleGapDetailsProps) => {
  const {} = props;

  return (
    <div className={cx('details')}>
      <VerticalGroup>
        <Text type="primary">Gaps this week</Text>
        <HorizontalGroup justify="space-between">
          <Text type="secondary">Number of gaps</Text>
          <Text type="secondary">12</Text>
        </HorizontalGroup>
        <HorizontalGroup justify="space-between">
          <Text type="secondary">Time</Text>
          <Text type="secondary">23h 12m</Text>
        </HorizontalGroup>
      </VerticalGroup>
    </div>
  );
};
