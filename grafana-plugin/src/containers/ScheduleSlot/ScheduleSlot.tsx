import React, { FC, useCallback, useEffect, useMemo } from 'react';

import { Button, HorizontalGroup, Icon, Tooltip, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';

import Avatar from 'components/Avatar/Avatar';
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
  handleOpenSchedule: (event: React.MouseEvent<HTMLDivElement>) => void;
  onShiftSwapClick: (id: ShiftSwap['id']) => void;
  color?: string;
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
    handleOpenSchedule,
    onShiftSwapClick,
    filters,
    onClick,
  } = props;

  const start = dayjs(event.start);
  const end = dayjs(event.end);

  const duration = end.diff(start, 'seconds');

  const base = 60 * 60 * 24 * 7;

  const width = duration / base;

  const currentMoment = useMemo(() => dayjs(), []);

  const renderEvent = (event): React.ReactElement | React.ReactElement[] => {
    if (event.shiftSwapId) {
      return <ShiftSwapEvent currentMoment={currentMoment} event={event} currentTimezone={currentTimezone} />;
    }

    if (event.is_gap) {
      return (
        <Tooltip content={<ScheduleGapDetails event={event} currentTimezone={currentTimezone} />}>
          <div className={cx('root', 'root__type_gap')} />
        </Tooltip>
      );
    }

    if (event.is_empty) {
      return (
        <div
          className={cx('root')}
          style={{
            backgroundColor: color,
          }}
        />
      );
    }

    return (
      <RegularEvent
        event={event}
        scheduleId={scheduleId}
        handleAddOverride={handleAddOverride}
        handleAddShiftSwap={handleAddShiftSwap}
        handleOpenSchedule={handleOpenSchedule}
        onShiftSwapClick={onShiftSwapClick}
        filters={filters}
        start={start}
        duration={duration}
        currentTimezone={currentTimezone}
        color={color}
        currentMoment={currentMoment}
      />
    );
  };

  return (
    <div className={cx('stack')} style={{ width: `${width * 100}%` }} onClick={onClick}>
      {renderEvent(event)}
    </div>
  );
});

export default ScheduleSlot;

interface ShiftSwapEventProps {
  event: Event;
  currentTimezone: Timezone;
  currentMoment: dayjs.Dayjs;
}

const ShiftSwapEvent = (props: ShiftSwapEventProps) => {
  const { event, currentTimezone, currentMoment } = props;

  const store = useStore();

  const shiftSwap = store.scheduleStore.shiftSwaps[event.shiftSwapId];

  useEffect(() => {
    if (shiftSwap?.beneficiary && !store.userStore.items[shiftSwap.beneficiary]) {
      store.userStore.updateItem(shiftSwap.beneficiary);
    }
  }, [shiftSwap?.beneficiary]);

  useEffect(() => {
    if (shiftSwap?.benefactor && !store.userStore.items[shiftSwap.benefactor]) {
      store.userStore.updateItem(shiftSwap.benefactor);
    }
  }, [shiftSwap?.benefactor]);

  const beneficiary = store.userStore.items[shiftSwap?.beneficiary];
  const benefactor = store.userStore.items[shiftSwap?.benefactor];

  const scheduleSlotContent = (
    <div className={cx('root', { 'root__type_shift-swap': true })}>
      {shiftSwap && (
        <HorizontalGroup spacing="xs">
          {beneficiary && <Avatar size="xs" src={beneficiary.avatar} />}
          {benefactor ? (
            <Avatar size="xs" src={benefactor.avatar} />
          ) : (
            <div className={cx('no-user')}>
              <Text size="xs" type="primary">
                ?
              </Text>
            </div>
          )}
        </HorizontalGroup>
      )}
    </div>
  );

  if (!shiftSwap) {
    return scheduleSlotContent;
  }

  return (
    <Tooltip
      interactive
      content={
        <ScheduleSlotDetails
          isShiftSwap
          beneficiaryName={beneficiary?.name}
          user={benefactor || beneficiary}
          benefactorName={benefactor?.name}
          currentTimezone={currentTimezone}
          event={event}
          color={SHIFT_SWAP_COLOR}
          currentMoment={currentMoment}
        />
      }
    >
      {scheduleSlotContent}
    </Tooltip>
  );
};

interface RegularEventProps {
  event: Event;
  scheduleId: Schedule['id'];
  currentTimezone: Timezone;
  handleAddOverride: (event: React.MouseEvent<HTMLDivElement>) => void;
  handleAddShiftSwap: (event: React.MouseEvent<HTMLDivElement>) => void;
  handleOpenSchedule: (event: React.MouseEvent<HTMLDivElement>) => void;
  onShiftSwapClick: (id: ShiftSwap['id']) => void;
  color?: string;
  filters?: ScheduleFiltersType;
  start: dayjs.Dayjs;
  duration: number;
  currentMoment: dayjs.Dayjs;
}

const RegularEvent = (props: RegularEventProps) => {
  const {
    event,
    scheduleId,
    onShiftSwapClick,
    filters,
    color,
    currentTimezone,
    start,
    duration,
    handleAddOverride,
    handleAddShiftSwap,
    handleOpenSchedule,
    currentMoment,
  } = props;
  const store = useStore();

  const { users } = event;

  const getShiftSwapClickHandler = useCallback(
    (swapId: ShiftSwap['id']) => {
      return (event: React.MouseEvent<HTMLDivElement>) => {
        event.stopPropagation();

        onShiftSwapClick(swapId);
      };
    },
    [onShiftSwapClick]
  );

  const onCallNow = store.scheduleStore.items[scheduleId]?.on_call_now;

  const enableWebOverrides = store.scheduleStore.items[scheduleId]?.enable_web_overrides;

  return (
    <>
      {users.map(({ display_name, pk: userPk, swap_request }) => {
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
                  !handleAddOverride ||
                  !enableWebOverrides ||
                  event.is_override ||
                  isShiftSwap ||
                  currentMoment.isAfter(dayjs(event.end))
                    ? undefined
                    : handleAddOverride
                }
                handleAddShiftSwap={
                  !handleAddShiftSwap || isShiftSwap || !isCurrentUserSlot || currentMoment.isAfter(dayjs(event.start))
                    ? undefined
                    : handleAddShiftSwap
                }
                handleOpenSchedule={handleOpenSchedule}
                color={backgroundColor}
                currentMoment={currentMoment}
              />
            }
          >
            {scheduleSlotContent}
          </Tooltip>
        );
      })}
    </>
  );
};

interface ScheduleSlotDetailsProps {
  user: User;
  isOncall?: boolean;
  currentTimezone: Timezone;
  event: Event;
  handleAddOverride?: (event: React.SyntheticEvent) => void;
  handleAddShiftSwap?: (event: React.SyntheticEvent) => void;
  handleOpenSchedule?: (event: React.SyntheticEvent) => void;
  color: string;
  isShiftSwap?: boolean;
  beneficiaryName?: string;
  benefactorName?: string;
  currentMoment: dayjs.Dayjs;
}

const ScheduleSlotDetails = (props: ScheduleSlotDetailsProps) => {
  const {
    user,
    currentTimezone,
    event,
    handleAddOverride,
    handleAddShiftSwap,
    handleOpenSchedule,
    color,
    isShiftSwap,
    beneficiaryName,
    benefactorName,
    currentMoment,
  } = props;

  const store = useStore();
  const { scheduleStore } = store;

  const shiftId = event.shift?.pk;

  const shift = scheduleStore.shifts[shiftId];

  useEffect(() => {
    if (shiftId && !scheduleStore.shifts[shiftId]) {
      scheduleStore.updateOncallShift(shiftId);
    }
  }, [shiftId]);

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
                {beneficiaryName} <Text type="secondary"> (requested by)</Text>
              </Text>
              {benefactorName ? (
                <Text type="primary" className={cx('username')}>
                  {benefactorName} <Text type="secondary"> (accepted by)</Text>
                </Text>
              ) : (
                <Text type="secondary" className={cx('username')}>
                  Not accepted yet
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
            {currentMoment.tz(user?.timezone).format('DD MMM, HH:mm')}
            <br />({getTzOffsetString(currentMoment.tz(user?.timezone))})
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
          {handleOpenSchedule && (
            <Button size="sm" variant="secondary" onClick={handleOpenSchedule}>
              Open schedule
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
