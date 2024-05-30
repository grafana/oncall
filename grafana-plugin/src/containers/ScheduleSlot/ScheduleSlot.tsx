import React, { FC, useCallback, useEffect, useMemo } from 'react';

import { css, cx } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { Button, HorizontalGroup, Icon, Tooltip, useStyles2, VerticalGroup } from '@grafana/ui';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';
import { COLORS, getLabelCss } from 'styles/utils.styles';

import NonExistentUserName from 'components/NonExistentUserName/NonExistentUserName';
import { RenderConditionally } from 'components/RenderConditionally/RenderConditionally';
import { ScheduleFiltersType } from 'components/ScheduleFilters/ScheduleFilters.types';
import { Text } from 'components/Text/Text';
import { WorkingHours } from 'components/WorkingHours/WorkingHours';
import { getShiftName, scheduleViewToDaysInOneRow, SHIFT_SWAP_COLOR } from 'models/schedule/schedule.helpers';
import { Event, ScheduleView, ShiftSwap } from 'models/schedule/schedule.types';
import { getTzOffsetString } from 'models/timezone/timezone.helpers';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useStore } from 'state/useStore';
import { truncateTitle } from 'utils/string';

import { getScheduleSlotStyleParams, getTitle } from './ScheduleSlot.helpers';

interface ScheduleSlotProps {
  event: Event;
  handleAddOverride: (event: React.MouseEvent<HTMLDivElement>) => void;
  handleAddShiftSwap: (event: React.MouseEvent<HTMLDivElement>) => void;
  handleOpenSchedule: (event: React.MouseEvent<HTMLDivElement>) => void;
  onShiftSwapClick: (id: ShiftSwap['id']) => void;
  color?: string;
  filters?: ScheduleFiltersType;
  onClick: (event: React.MouseEvent<HTMLDivElement>) => void;
  showScheduleNameAsSlotTitle?: boolean;
  scheduleView?: ScheduleView;
}

export const ScheduleSlot: FC<ScheduleSlotProps> = observer((props) => {
  const {
    timezoneStore: { getDateInSelectedTimezone },
    scheduleStore: { scheduleView: storeScheduleView },
  } = useStore();
  const styles = useStyles2(getStyles);

  const {
    event,
    color,
    handleAddOverride,
    handleAddShiftSwap,
    handleOpenSchedule,
    onShiftSwapClick,
    filters,
    onClick,
    showScheduleNameAsSlotTitle,
    scheduleView: propsScheduleView,
  } = props;

  const scheduleView = propsScheduleView || storeScheduleView;

  const start = getDateInSelectedTimezone(event.start);
  const end = getDateInSelectedTimezone(event.end);

  const durationInSeconds = end.diff(start, 'seconds');

  const rowInSeconds = scheduleViewToDaysInOneRow[scheduleView] * 24 * 60 * 60;

  const width = Math.max(durationInSeconds / rowInSeconds, 0);

  const currentMoment = useMemo(() => dayjs(), []);

  const renderEvent = (event: Event): React.ReactElement | React.ReactElement[] => {
    if (event.shiftSwapId) {
      return <ShiftSwapEvent currentMoment={currentMoment} event={event} />;
    }

    if (event.is_gap) {
      return (
        <Tooltip content={<ScheduleGapDetails event={event} />}>
          <div className={cx(styles.root, styles.gap)} />
        </Tooltip>
      );
    }

    if (event.is_empty) {
      return (
        <RenderConditionally
          shouldRender={event.missing_users.length > 0}
          backupChildren={
            <div
              className={styles.root}
              style={{
                backgroundColor: color,
              }}
            />
          }
        >
          {event.missing_users.map((name) => (
            <div
              key={name}
              className={styles.root}
              style={{
                backgroundColor: color,
              }}
            >
              <div className={styles.title}>
                <NonExistentUserName userName={name} />
              </div>
            </div>
          ))}
        </RenderConditionally>
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
        duration={durationInSeconds}
        color={color}
        currentMoment={currentMoment}
        showScheduleNameAsSlotTitle={showScheduleNameAsSlotTitle}
      />
    );
  };

  return (
    <div className={styles.stack} style={{ width: `${width * 100}%` }} onClick={onClick}>
      {renderEvent(event)}
    </div>
  );
});

interface ShiftSwapEventProps {
  event: Event;
  currentMoment: dayjs.Dayjs;
}

const ShiftSwapEvent = (props: ShiftSwapEventProps) => {
  const { event, currentMoment } = props;

  const store = useStore();
  const styles = useStyles2(getStyles);

  const shiftSwap = store.scheduleStore.shiftSwaps[event.shiftSwapId];

  const beneficiary = shiftSwap?.beneficiary;
  const benefactor = shiftSwap?.benefactor;

  useEffect(() => {
    if (shiftSwap?.beneficiary && !store.userStore.items[shiftSwap.beneficiary.pk]) {
      store.userStore.fetchItemById({ userPk: shiftSwap.beneficiary.pk, skipIfAlreadyPending: true });
    }
  }, [shiftSwap?.beneficiary]);

  useEffect(() => {
    if (shiftSwap?.benefactor && !store.userStore.items[shiftSwap.benefactor.pk]) {
      store.userStore.fetchItemById({ userPk: shiftSwap.benefactor.pk, skipIfAlreadyPending: true });
    }
  }, [shiftSwap?.benefactor]);

  const beneficiaryStoreUser = store.userStore.items[shiftSwap?.beneficiary?.pk];
  const benefactorStoreUser = store.userStore.items[shiftSwap?.benefactor?.pk];

  const { backgroundColor, border, textColor } = getScheduleSlotStyleParams(
    SHIFT_SWAP_COLOR,
    true,
    Boolean(shiftSwap?.benefactor)
  );

  const scheduleSlotContent = (
    <div
      className={cx(styles.root)}
      style={{
        backgroundColor,
        border,
        color: textColor,
      }}
      data-testid="schedule-slot"
    >
      {shiftSwap && (
        <div className={styles.title}>
          {truncateTitle(beneficiary.display_name, 9)} → {benefactor ? truncateTitle(benefactor.display_name, 9) : '?'}
        </div>
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
    color: propsColor,
    start,
    duration,
    handleAddOverride,
    handleAddShiftSwap,
    handleOpenSchedule,
    currentMoment,
    showScheduleNameAsSlotTitle,
  } = props;
  const store = useStore();
  const styles = useStyles2(getStyles);

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

        const { schedule, shift } = event;

        const isCurrentUserSlot = userPk === store.userStore.currentUserPk;
        const inactive = filters && filters.users.length && !filters.users.includes(userPk);

        const userTitle = showScheduleNameAsSlotTitle ? schedule?.name : storeUser ? getTitle(storeUser) : display_name;

        const isShiftSwap = Boolean(swap_request);

        const title = isShiftSwap
          ? `Shift swap to ${getShiftName(shift)}`
          : showScheduleNameAsSlotTitle
          ? schedule?.name
          : getShiftName(shift);

        const { color, backgroundColor, border, textColor } = getScheduleSlotStyleParams(
          propsColor,
          Boolean(swap_request),
          Boolean(swap_request?.user)
        );

        const scheduleSlotContent = (
          <div
            className={cx(styles.root, { [styles.inactive]: inactive })}
            style={{
              backgroundColor,
              border,
              color: textColor,
            }}
            onClick={swap_request ? getShiftSwapClickHandler(swap_request.pk) : undefined}
            data-testid="schedule-slot"
          >
            {storeUser && (!swap_request || swap_request.user) && (
              <WorkingHours
                className={styles.workingHours}
                timezone={storeUser.timezone}
                workingHours={storeUser.working_hours}
                startMoment={start}
                duration={duration}
              />
            )}
            <div className={styles.title}>
              {swap_request && !swap_request.user ? truncateTitle(userTitle, 9) + ' → ?' : userTitle}
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
                color={color}
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
  user: ApiSchemas['User'];
  isOncall?: boolean;
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

const ScheduleSlotDetails = observer((props: ScheduleSlotDetailsProps) => {
  const {
    user,
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

  const {
    scheduleStore,
    timezoneStore: { currentDateInSelectedTimezone, getDateInSelectedTimezone },
  } = useStore();

  const shiftId = event.shift?.pk;
  const shift = scheduleStore.shifts[shiftId];

  const schedule = scheduleStore.items[shift?.schedule];

  const enableWebOverrides = schedule?.enable_web_overrides;

  const styles = useStyles2(getStyles);

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
    <div className={styles.details}>
      <VerticalGroup>
        <HorizontalGroup>
          <div className={styles.detailsIcon}>
            <div className={styles.badge} style={{ backgroundColor: color }} />
          </div>
          <Text type="primary" maxWidth="222px">
            {title}
          </Text>
        </HorizontalGroup>
        <HorizontalGroup align="flex-start">
          <div className={styles.detailsIcon}>
            <Icon className={styles.icon} name={isShiftSwap ? 'user-arrows' : 'user'} />
          </div>
          {isShiftSwap ? (
            <VerticalGroup spacing="xs">
              <Text type="primary">Swap pair</Text>
              <Text type="primary" className={styles.username}>
                {beneficiaryName} <Text type="secondary"> (requested by)</Text>
              </Text>
              {benefactorName ? (
                <Text type="primary" className={styles.username}>
                  {benefactorName} <Text type="secondary"> (accepted by)</Text>
                </Text>
              ) : (
                <Text type="secondary" className={styles.username}>
                  Not accepted yet
                </Text>
              )}
            </VerticalGroup>
          ) : (
            <Text type="primary" className={styles.username}>
              {user?.username}
            </Text>
          )}
        </HorizontalGroup>
        <HorizontalGroup align="flex-start">
          <div className={styles.detailsIcon}>
            <Icon className={styles.icon} name="clock-nine" />
          </div>
          <Text type="primary" className={styles.secondColumn} data-testid="schedule-slot-user-local-time">
            User's local time
            <br />
            {currentMoment.tz(user?.timezone).format('DD MMM, HH:mm')}
            <br />({user?.timezone})
          </Text>
          <Text type="secondary" data-testid="schedule-slot-current-timezone">
            Current timezone
            <br />
            {currentDateInSelectedTimezone.format('DD MMM, HH:mm')}
            <br />({getTzOffsetString(currentDateInSelectedTimezone)})
          </Text>
        </HorizontalGroup>
        <HorizontalGroup align="flex-start">
          <div className={styles.detailsIcon}>
            <Icon className={styles.icon} name="arrows-h" />
          </div>
          <Text type="primary" className={styles.secondColumn}>
            This shift
            <br />
            {dayjs(event.start).tz(user?.timezone).format('DD MMM, HH:mm')}
            <br />
            {dayjs(event.end).tz(user?.timezone).format('DD MMM, HH:mm')}
          </Text>
          <Text type="secondary">
            &nbsp; <br />
            {getDateInSelectedTimezone(dayjs(event.start)).format('DD MMM, HH:mm')}
            <br />
            {getDateInSelectedTimezone(dayjs(event.end)).format('DD MMM, HH:mm')}
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
});

interface ScheduleGapDetailsProps {
  event: Event;
}

const ScheduleGapDetails = observer((props: ScheduleGapDetailsProps) => {
  const styles = useStyles2(getStyles);
  const {
    timezoneStore: { selectedTimezoneLabel, getDateInSelectedTimezone },
  } = useStore();
  const { event } = props;

  return (
    <div className={styles.details}>
      <VerticalGroup>
        <HorizontalGroup spacing="sm">
          <VerticalGroup spacing="none">
            <Text type="primary">{selectedTimezoneLabel}</Text>
            <Text type="primary">{getDateInSelectedTimezone(dayjs(event.start)).format('DD MMM, HH:mm')}</Text>
            <Text type="primary">{getDateInSelectedTimezone(dayjs(event.end)).format('DD MMM, HH:mm')}</Text>
          </VerticalGroup>
        </HorizontalGroup>
      </VerticalGroup>
    </div>
  );
});

const getStyles = (theme: GrafanaTheme2) => {
  return {
    root: css`
      height: 28px;
      background: ${COLORS.GRAY_8};
      border-radius: 2px;
      position: relative;
      display: flex;
      overflow: hidden;
      margin-right: 1px;
      padding: 4px;
      align-items: center;
      transition: opacity 0.2s ease;
      cursor: pointer;
    `,

    workingHours: css`
      position: absolute;
      top: 0;
      left: 0;
      pointer-events: none;
    `,

    stack: css`
      display: flex;
      flex-direction: column;
      gap: 1px;
      flex-shrink: 0;
    `,

    // TODO: What would be a matching value from theme for background?
    gap: css`
      background: rgba(209, 14, 92, 0.2);
      border: 1px dashed ${theme.colors.error.text};
      color: rgba(209, 14, 92, 0.5);
      visibility: hidden;
    `,

    noUser: css`
      width: 12px;
      height: 12px;
      background: ${getLabelCss('blue', theme)};
      border-radius: 50%;
      display: flex;
      justify-content: center;
    `,

    inactive: css`
      opacity: 0.3;
    `,

    title: css`
      z-index: 1;
      font-size: 12px;
      width: 100%;
      font-weight: 500;
      white-space: nowrap;
    `,

    label: css`
      background: rgba(255, 255, 255, 0.7);
      border-radius: 2px;
      display: inline-block;
      padding: 2px 4px;
      line-height: 16px;
      z-index: 1;
      font-size: 10px;
      font-weight: bold;
      margin-right: 5px;
      flex-shrink: 0;
    `,

    details: css`
      width: 300px;
      padding: 5px 0;
    `,

    detailsUserStatus: css`
      width: 10px;
      height: 10px;
      border-radius: 50%;

      &--success {
        background-color: ${theme.colors.success.text};
      }
    `,

    time: css`
      position: absolute;
      top: 0;
      bottom: 0;
      width: 1px;
      background-color: white;
      z-index: 2;
    `,

    isOnCallIcon: css`
      color: ${theme.isDark ? '#181b1f' : '#fff'};
      vertical-align: middle;
    `,

    detailsIcon: css`
      width: 16px;
      margin-right: 4px;
    `,

    badge: css`
      width: 8px;
      height: 8px;
      border-radius: 50%;
      margin: 0 auto;
    `,

    username: css`
      word-break: break-word;
    `,

    secondColumn: css`
      width: 120px;
    `,

    icon: css`
      color: ${theme.colors.secondary.text};
    `,
  };
};
