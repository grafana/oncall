import React, { FC, useCallback, useMemo } from 'react';

import { Button, HorizontalGroup, Icon, Tooltip, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';

import { ScheduleFiltersType } from 'components/ScheduleFilters/ScheduleFilters.types';
import Text from 'components/Text/Text';
import WorkingHours from 'components/WorkingHours/WorkingHours';
import { getShiftName, SHIFT_SWAP_COLOR } from 'models/schedule/schedule.helpers';
import { Event, Schedule, ShiftSwap } from 'models/schedule/schedule.types';
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
  handleAddOverride: (event: React.MouseEvent<HTMLDivElement>) => void;
  handleAddShiftSwap: (event: React.MouseEvent<HTMLDivElement>) => void;
  onShiftSwapClick: (id: ShiftSwap['id']) => void;
  color?: string;
  simplified?: boolean;
  filters?: ScheduleFiltersType;
  onClick: (event: React.MouseEvent<HTMLDivElement>) => void;
}

const cx = cn.bind(styles);

const ScheduleSlot: FC<ScheduleSlotProps> = observer((props) => {
  const {
    event,
    scheduleId,
    currentTimezone,
    color,
    handleAddOverride,
    handleAddShiftSwap,
    onShiftSwapClick,
    simplified,
    filters,
    onClick,
  } = props;
  const { users } = event;

  const getShiftSwapClickHandler = useCallback((swapId: ShiftSwap['id']) => {
    return (event: React.MouseEvent<HTMLDivElement>) => {
      event.stopPropagation();

      onShiftSwapClick(swapId);
    };
  }, []);

  const start = dayjs(event.start);
  const end = dayjs(event.end);

  const duration = end.diff(start, 'seconds');

  const store = useStore();

  const base = 60 * 60 * 24 * 7;

  const width = duration / base;

  const onCallNow = store.scheduleStore.items[scheduleId]?.on_call_now;

  const enableWebOverrides = store.scheduleStore.items[scheduleId]?.enable_web_overrides;

  return (
    <div className={cx('stack')} style={{ width: `${width * 100}%` }} onClick={onClick}>
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
        users.map(({ display_name, pk: userPk, swap_request }) => {
          const storeUser = store.userStore.items[userPk];

          const isCurrentUserSlot = userPk === store.userStore.currentUserPk;
          const inactive = filters && filters.users.length && !filters.users.includes(userPk);

          const title = storeUser ? getTitle(storeUser) : display_name;

          const isOncall = Boolean(
            storeUser && onCallNow && onCallNow.some((onCallUser) => storeUser.pk === onCallUser.pk)
          );

          const isShiftSwap = Boolean(swap_request);

          let backgroundColor = color;
          if (isShiftSwap) {
            backgroundColor = SHIFT_SWAP_COLOR;
          }

          const scheduleSlotContent = (
            <div
              className={cx('root', { root__inactive: inactive })}
              style={{
                backgroundColor,
              }}
              onClick={swap_request ? getShiftSwapClickHandler(swap_request.pk) : undefined}
            >
              {storeUser && (!swap_request || swap_request.user) && (
                <WorkingHours
                  className={cx('working-hours')}
                  timezone={storeUser.timezone}
                  workingHours={storeUser.working_hours}
                  startMoment={start}
                  duration={duration}
                />
              )}
              <div className={cx('title')}>
                {swap_request && !swap_request.user ? <Icon name="user-arrows" /> : title}
              </div>
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
                  isShiftSwap={isShiftSwap}
                  beneficiaryName={
                    isShiftSwap ? (swap_request.user ? swap_request.user.display_name : display_name) : undefined
                  }
                  benefactorName={isShiftSwap ? (swap_request.user ? display_name : undefined) : undefined}
                  user={storeUser}
                  isOncall={isOncall}
                  currentTimezone={currentTimezone}
                  event={event}
                  handleAddOverride={
                    !enableWebOverrides || simplified || event.is_override || isShiftSwap
                      ? undefined
                      : handleAddOverride
                  }
                  handleAddShiftSwap={simplified || isShiftSwap || !isCurrentUserSlot ? undefined : handleAddShiftSwap}
                  simplified={simplified}
                  color={backgroundColor}
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
  handleAddShiftSwap: (event: React.SyntheticEvent) => void;
  simplified?: boolean;
  color: string;
  isShiftSwap?: boolean;
  beneficiaryName?: string;
  benefactorName?: string;
}

const ScheduleSlotDetails = (props: ScheduleSlotDetailsProps) => {
  const {
    user,
    currentTimezone,
    event,
    handleAddOverride,
    handleAddShiftSwap,
    color,
    isShiftSwap,
    beneficiaryName,
    benefactorName,
  } = props;

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
            {isShiftSwap ? 'Shift swap' : getShiftName(shift)}
          </Text>
        </HorizontalGroup>
        <HorizontalGroup align="flex-start">
          <div className={cx('details-icon')}>
            <Icon className={cx('icon')} name={isShiftSwap ? 'user-arrows' : 'user'} />
          </div>
          {isShiftSwap ? (
            <VerticalGroup spacing="xs">
              <Text type="primary">Swap pair</Text>
              <Text type="primary" className={cx('username')}>
                {beneficiaryName} <Text type="secondary">(creator)</Text>
              </Text>
              {benefactorName ? (
                <Text type="primary" className={cx('username')}>
                  {benefactorName} <Text type="secondary">(taken by)</Text>
                </Text>
              ) : (
                <Text type="secondary" className={cx('username')}>
                  Not taken yet
                </Text>
              )}
            </VerticalGroup>
          ) : (
            <Text type="primary" className={cx('username')}>
              {user?.username}
            </Text>
          )}
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
        <HorizontalGroup justify="flex-end">
          {handleAddShiftSwap && (
            <Button size="sm" variant="secondary" onClick={handleAddShiftSwap}>
              Request shift swap
            </Button>
          )}
          {handleAddOverride && (
            <Button size="sm" variant="secondary" onClick={handleAddOverride}>
              + Override
            </Button>
          )}
        </HorizontalGroup>
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
