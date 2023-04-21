import React, { FC } from 'react';

import { Button, HorizontalGroup, Tooltip, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';

import { ScheduleFiltersType } from 'components/ScheduleFilters/ScheduleFilters.types';
import Line from 'components/ScheduleUserDetails/img/line.svg';
import Text from 'components/Text/Text';
import WorkingHours from 'components/WorkingHours/WorkingHours';
import { IsOncallIcon } from 'icons';
import { getShiftTitle } from 'models/schedule/schedule.helpers';
import { Event, Schedule } from 'models/schedule/schedule.types';
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
  label?: string;
  simplified?: boolean;
  filters?: ScheduleFiltersType;
}

const cx = cn.bind(styles);

const ScheduleSlot: FC<ScheduleSlotProps> = observer((props) => {
  const { event, scheduleId, currentTimezone, color, label, handleAddOverride, simplified, filters } = props;
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
          <div className={cx('root', 'root__type_gap')} style={{}}>
            {label && <div className={cx('label')}>{label}</div>}
          </div>
        </Tooltip>
      ) : event.is_empty ? (
        <div
          className={cx('root')}
          style={{
            backgroundColor: color,
          }}
        >
          {label && (
            <div className={cx('label')} style={{ color }}>
              {label}
            </div>
          )}
        </div>
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
  const { user, currentTimezone, event, isOncall, handleAddOverride, simplified, color } = props;

  const store = useStore();
  const { scheduleStore } = store;

  const shift = scheduleStore.shifts[event.shift?.pk];

  console.log('shift', shift);

  return (
    <div className={cx('details')}>
      <VerticalGroup>
        <HorizontalGroup>
          <div className={cx('badge')} style={{ backgroundColor: color }} />
          <Text className={cx('details-title')} type="primary">
            {getShiftTitle(shift)}
            {/* property only affects content that is overflowing a block container element in its */}
          </Text>
        </HorizontalGroup>
        <HorizontalGroup>
          <VerticalGroup spacing="sm">
            <HorizontalGroup spacing="sm">
              {isOncall && <IsOncallIcon className={cx('is-oncall-icon')} />}
              <Text type="secondary">{user?.username}</Text>
            </HorizontalGroup>
            <HorizontalGroup>
              <VerticalGroup spacing="none">
                <HorizontalGroup spacing="sm">
                  <img src={Line} />
                  <VerticalGroup spacing="none">
                    <Text type="secondary">{dayjs(event.start).tz(user?.timezone).format('DD MMM, HH:mm')}</Text>
                    <Text type="secondary">{dayjs(event.end).tz(user?.timezone).format('DD MMM, HH:mm')}</Text>
                  </VerticalGroup>
                </HorizontalGroup>
              </VerticalGroup>
            </HorizontalGroup>
          </VerticalGroup>
          <VerticalGroup spacing="sm">
            <Text type="primary">{currentTimezone}</Text>
            <VerticalGroup spacing="none">
              <Text type="primary">{dayjs(event.start).tz(currentTimezone).format('DD MMM, HH:mm')}</Text>
              <Text type="primary">{dayjs(event.end).tz(currentTimezone).format('DD MMM, HH:mm')}</Text>
            </VerticalGroup>
          </VerticalGroup>
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
