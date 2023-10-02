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
import { Event, ShiftSwap } from 'models/schedule/schedule.types';
import { getTzOffsetString } from 'models/timezone/timezone.helpers';
import { Timezone } from 'models/timezone/timezone.types';
import { User } from 'models/user/user.types';
import { useStore } from 'state/useStore';

import { getTitle } from './ScheduleSlot.helpers';

import styles from './ScheduleSlot.module.css';

interface ScheduleSlotProps {
  event: Event;
  startMoment: dayjs.Dayjs;
  currentTimezone: Timezone;
  handleAddOverride: (event: React.MouseEvent<HTMLDivElement>) => void;
  handleAddShiftSwap: (event: React.MouseEvent<HTMLDivElement>) => void;
  handleOpenSchedule: (event: React.MouseEvent<HTMLDivElement>) => void;
  onShiftSwapClick: (id: ShiftSwap['id']) => void;
  color?: string;
  filters?: ScheduleFiltersType;
  onClick: (event: React.MouseEvent<HTMLDivElement>) => void;
  showScheduleNameAsSlotTitle?: boolean;
}

const cx = cn.bind(styles);

const ScheduleSlot: FC<ScheduleSlotProps> = observer((props) => {
  const {
    event,
    currentTimezone,
    color,
    handleAddOverride,
    handleAddShiftSwap,
    handleOpenSchedule,
    onShiftSwapClick,
    filters,
    onClick,
    showScheduleNameAsSlotTitle,
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
        showScheduleNameAsSlotTitle={showScheduleNameAsSlotTitle}
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

  const beneficiary = shiftSwap?.beneficiary;
  const benefactor = shiftSwap?.benefactor;

  useEffect(() => {
    if (shiftSwap?.beneficiary && !store.userStore.items[shiftSwap.beneficiary.pk]) {
      store.userStore.updateItem(shiftSwap.beneficiary.pk);
    }
  }, [shiftSwap?.beneficiary]);

  useEffect(() => {
    if (shiftSwap?.benefactor && !store.userStore.items[shiftSwap.benefactor.pk]) {
      store.userStore.updateItem(shiftSwap.benefactor.pk);
    }
  }, [shiftSwap?.benefactor]);

  const beneficiaryStoreUser = store.userStore.items[shiftSwap?.beneficiary?.pk];
  const benefactorStoreUser = store.userStore.items[shiftSwap?.benefactor?.pk];

  const scheduleSlotContent = (
    <div className={cx('root', { 'root__type_shift-swap': true })}>
      {shiftSwap && (
        <HorizontalGroup spacing="xs">
          {beneficiary && <Avatar size="xs" src={beneficiary.avatar_full} />}
          {benefactor ? (
            <Avatar size="xs" src={benefactor.avatar_full} />
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
          title="Shift swap"
          beneficiaryName={beneficiary?.display_name}
          user={benefactorStoreUser || beneficiaryStoreUser}
          benefactorName={benefactor?.display_name}
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
  showScheduleNameAsSlotTitle: boolean;
}

const RegularEvent = (props: RegularEventProps) => {
  const {
    event,
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
    showScheduleNameAsSlotTitle,
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

  return (
    <>
      {users.map(({ display_name, pk: userPk, swap_request }) => {
        const storeUser = store.userStore.items[userPk];

        const shiftId = event.shift?.pk;
        const shift = store.scheduleStore.shifts[shiftId];

        /* if (shiftId && !store.scheduleStore.shifts[shiftId]) {
          store.scheduleStore.updateOncallShift(shiftId);
        }
 */
        const { schedule } = event;

        const isCurrentUserSlot = userPk === store.userStore.currentUserPk;
        const inactive = filters && filters.users.length && !filters.users.includes(userPk);

        const userTitle = showScheduleNameAsSlotTitle ? schedule?.name : storeUser ? getTitle(storeUser) : display_name;

        const isShiftSwap = Boolean(swap_request);

        const title = isShiftSwap ? 'Shift swap' : showScheduleNameAsSlotTitle ? schedule?.name : getShiftName(shift);

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
              {swap_request && !swap_request.user ? <Icon name="user-arrows" /> : userTitle}
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
                title={title}
                isShiftSwap={isShiftSwap}
                beneficiaryName={
                  isShiftSwap ? (swap_request.user ? swap_request.user.display_name : display_name) : undefined
                }
                benefactorName={isShiftSwap ? (swap_request.user ? display_name : undefined) : undefined}
                user={storeUser}
                currentTimezone={currentTimezone}
                event={event}
                handleAddOverride={
                  !handleAddOverride || event.is_override || isShiftSwap || currentMoment.isAfter(dayjs(event.end))
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
  title: string;
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
    title,
  } = props;

  const { scheduleStore } = useStore();

  const shiftId = event.shift?.pk;
  const shift = scheduleStore.shifts[shiftId];

  const schedule = scheduleStore.items[shift?.schedule];

  const enableWebOverrides = schedule?.enable_web_overrides;

  useEffect(() => {
    if (shiftId && !scheduleStore.shifts[shiftId]) {
      scheduleStore.updateOncallShift(shiftId);
    }
  }, [shiftId]);

  useEffect(() => {
    if (shift && !scheduleStore.items[shift.schedule]) {
      scheduleStore.loadItem(shift.schedule);
    }
  }, [shift]);

  // const onCallNow = schedule?.on_call_now;
  // const isOncall = Boolean(storeUser && onCallNow && onCallNow.some((onCallUser) => storeUser.pk === onCallUser.pk));

  return (
    <div className={cx('details')}>
      <VerticalGroup>
        <HorizontalGroup>
          <div className={cx('details-icon')}>
            <div className={cx('badge')} style={{ backgroundColor: color }} />
          </div>
          <Text type="primary" maxWidth="222px">
            {title}
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
          {handleAddOverride && enableWebOverrides && (
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
