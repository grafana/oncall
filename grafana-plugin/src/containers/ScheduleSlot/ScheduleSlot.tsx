import React, { FC, useMemo } from 'react';

import { Button, HorizontalGroup, Icon, Tooltip, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';

import { ScheduleFiltersType } from 'components/ScheduleFilters/ScheduleFilters.types';
import Text from 'components/Text/Text';
import WorkingHours from 'components/WorkingHours/WorkingHours';
import { getShiftTitle } from 'models/schedule/schedule.helpers';
import { Event, Schedule } from 'models/schedule/schedule.types';
import { getTzOffsetString } from 'models/timezone/timezone.helpers';
import { Timezone } from 'models/timezone/timezone.types';
import { User } from 'models/user/user.types';
import { useStore } from 'state/useStore';

import { getTitle } from './ScheduleSlot.helpers';

import styles from './ScheduleSlot.module.css';

interface ScheduleSlotProps {
  event: Event;
  scheduleId: Schedule['id'];
  startMoment: dayjs.Dayjs;
  currentTimezone: Timezone;
  handleAddOverride: (event: React.SyntheticEvent) => void;
  color?: string;
  simplified?: boolean;
  filters?: ScheduleFiltersType;
}

const cx = cn.bind(styles);

const ScheduleSlot: FC<ScheduleSlotProps> = observer((props) => {
  const { event, scheduleId, currentTimezone, color, handleAddOverride, simplified, filters } = props;
  const { users } = event;

  const start = dayjs(event.start);
  const end = dayjs(event.end);

  const duration = end.diff(start, 'seconds');

  const store = useStore();

  const base = 60 * 60 * 24 * 7;

  const width = duration / base;

  const onCallNow = store.scheduleStore.items[scheduleId]?.on_call_now;

  return (
    <div className={cx('stack')} style={{ width: `${width * 100}%` }}>
      {event.is_gap ? (
        <Tooltip content={<ScheduleGapDetails event={event} currentTimezone={currentTimezone} />}>
          <div className={cx('root', 'root__type_gap')} />
        </Tooltip>
      ) : event.is_empty ? (
        <div
          className={cx('root')}
          style={{
            backgroundColor: color,
          }}
        />
      ) : (
        users.map(({ display_name, pk: userPk }) => {
          const storeUser = store.userStore.items[userPk];

          const inactive = filters && filters.users.length && !filters.users.includes(userPk);

          const title = storeUser ? getTitle(storeUser) : display_name;

          const isOncall = Boolean(
            storeUser && onCallNow && onCallNow.some((onCallUser) => storeUser.pk === onCallUser.pk)
          );

          const scheduleSlotContent = (
            <div
              className={cx('root', { root__inactive: inactive })}
              style={{
                backgroundColor: color,
              }}
            >
              {storeUser && (
                <WorkingHours
                  className={cx('working-hours')}
                  timezone={storeUser.timezone}
                  workingHours={storeUser.working_hours}
                  startMoment={start}
                  duration={duration}
                />
              )}
              <div className={cx('title')}>{title}</div>
            </div>
          );

          if (!storeUser) {
            return scheduleSlotContent;
          } // show without a tooltip as we're lacking user info

          return (
            <Tooltip
              interactive
              key={userPk}
              content={
                <ScheduleSlotDetails
                  user={storeUser}
                  isOncall={isOncall}
                  currentTimezone={currentTimezone}
                  event={event}
                  handleAddOverride={handleAddOverride}
                  simplified={simplified}
                  color={color}
                />
              }
            >
              {scheduleSlotContent}
            </Tooltip>
          );
        })
      )}
    </div>
  );
});

export default ScheduleSlot;

interface ScheduleSlotDetailsProps {
  user: User;
  isOncall: boolean;
  currentTimezone: Timezone;
  event: Event;
  handleAddOverride: (event: React.SyntheticEvent) => void;
  simplified?: boolean;
  color: string;
}

const ScheduleSlotDetails = (props: ScheduleSlotDetailsProps) => {
  const { user, currentTimezone, event, handleAddOverride, simplified, color } = props;

  const store = useStore();
  const { scheduleStore } = store;

  const currentMoment = useMemo(() => dayjs(), []);

  const shift = scheduleStore.shifts[event.shift?.pk];

  return (
    <div className={cx('details')}>
      <VerticalGroup>
        <HorizontalGroup>
          <div className={cx('details-icon')}>
            <div className={cx('badge')} style={{ backgroundColor: color }} />
          </div>
          <Text type="primary" maxWidth="222px">
            {getShiftTitle(shift)}
          </Text>
        </HorizontalGroup>
        <HorizontalGroup align="flex-start">
          <div className={cx('details-icon')}>
            <Icon className={cx('icon')} name="user" />
          </div>
          <Text type="primary" className={cx('username')}>
            {user?.username}
          </Text>
        </HorizontalGroup>
        <HorizontalGroup align="flex-start">
          <div className={cx('details-icon')}>
            <Icon className={cx('icon')} name="clock-nine" />
          </div>
          <Text type="primary" className={cx('second-column')}>
            User local time
            <br />
            {currentMoment.tz(user.timezone).format('DD MMM, HH:mm')}
            <br />({getTzOffsetString(currentMoment.tz(user.timezone))})
          </Text>
          <Text type="secondary">
            Current timezone
            <br />
            {currentMoment.tz(currentTimezone).format('DD MMM, HH:mm')}
            <br />({getTzOffsetString(currentMoment.tz(currentTimezone))})
          </Text>
        </HorizontalGroup>
        <HorizontalGroup align="flex-start">
          <div className={cx('details-icon')}>
            <Icon className={cx('icon')} name="arrows-h" />
          </div>
          <Text type="primary" className={cx('second-column')}>
            This shift
            <br />
            {dayjs(event.start).tz(user?.timezone).format('DD MMM, HH:mm')}
            <br />
            {dayjs(event.end).tz(user?.timezone).format('DD MMM, HH:mm')}
          </Text>
          <Text type="secondary">
            &nbsp; <br />
            {dayjs(event.start).tz(currentTimezone).format('DD MMM, HH:mm')}
            <br />
            {dayjs(event.end).tz(currentTimezone).format('DD MMM, HH:mm')}
          </Text>
        </HorizontalGroup>
        {!simplified && !event.is_override && (
          <HorizontalGroup justify="flex-end">
            <Button size="sm" variant="secondary" onClick={handleAddOverride}>
              + Override
            </Button>
          </HorizontalGroup>
        )}
      </VerticalGroup>
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
      </VerticalGroup>
    </div>
  );
};
