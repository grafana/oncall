import React, { FC, useEffect } from 'react';

import { Badge, Button, HorizontalGroup, Icon } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import { RouteComponentProps, withRouter } from 'react-router-dom';
import { CSSTransition, TransitionGroup } from 'react-transition-group';

import { Avatar } from 'components/Avatar/Avatar';
import { Text } from 'components/Text/Text';
import { Rotation } from 'containers/Rotation/Rotation';
import { TimelineMarks } from 'containers/TimelineMarks/TimelineMarks';
import { ActionKey } from 'models/loader/action-keys';
import { getColorForSchedule, getPersonalShiftsFromStore } from 'models/schedule/schedule.helpers';
import { Event } from 'models/schedule/schedule.types';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { getStartOfWeekBasedOnCurrentDate } from 'pages/schedule/Schedule.helpers';
import { useStore } from 'state/useStore';
import { PLUGIN_ROOT } from 'utils/consts';
import { useIsLoading } from 'utils/hooks';

import { DEFAULT_TRANSITION_TIMEOUT } from './Rotations.config';

import styles from './Rotations.module.css';

const cx = cn.bind(styles);

interface SchedulePersonalProps extends RouteComponentProps {
  userPk: ApiSchemas['User']['pk'];
  onSlotClick?: (event: Event) => void;
}

const _SchedulePersonal: FC<SchedulePersonalProps> = observer(({ userPk, onSlotClick, history }) => {
  const store = useStore();
  const { timezoneStore, scheduleStore, userStore } = store;
  const updatePersonalEventsLoading = useIsLoading(ActionKey.UPDATE_PERSONAL_EVENTS);

  useEffect(() => {
    updatePersonalEvents();
  }, [timezoneStore.selectedTimezoneOffset]);

  const updatePersonalEvents = () => {
    scheduleStore.updatePersonalEvents(userStore.currentUserPk, timezoneStore.calendarStartDate, 9, true);
  };

  const handleTodayClick = () => {
    timezoneStore.setCalendarStartDate(getStartOfWeekBasedOnCurrentDate(timezoneStore.currentDateInSelectedTimezone));
  };

  const handleLeftClick = () => {
    timezoneStore.setCalendarStartDate(timezoneStore.calendarStartDate.subtract(7, 'day'));
    scheduleStore.updatePersonalEvents(userStore.currentUserPk, timezoneStore.calendarStartDate);
  };

  const handleRightClick = () => {
    timezoneStore.setCalendarStartDate(timezoneStore.calendarStartDate.add(7, 'day'));
    scheduleStore.updatePersonalEvents(userStore.currentUserPk, timezoneStore.calendarStartDate);
  };

  const openSchedule = (event: Event) => {
    history.push(`${PLUGIN_ROOT}/schedules/${event.schedule?.id}`);
  };

  const base = 7 * 24 * 60; // in minutes
  const diff = timezoneStore.currentDateInSelectedTimezone.diff(timezoneStore.calendarStartDate, 'minutes');

  const currentTimeX = diff / base;

  const shifts = getPersonalShiftsFromStore(store, userPk, timezoneStore.calendarStartDate);

  const currentTimeHidden = currentTimeX < 0 || currentTimeX > 1;

  const getColor = (event: Event) => getColorForSchedule(event.schedule?.id);

  const isOncall = scheduleStore.onCallNow[userPk];

  const storeUser = userStore.items[userPk];

  const emptyRotationsText = updatePersonalEventsLoading ? 'Loading ...' : 'There are no schedules relevant to user';

  return (
    <div className={cx('root')}>
      <div className={cx('header')}>
        <div className={cx('title')}>
          <HorizontalGroup justify="space-between">
            <HorizontalGroup>
              <Text type="secondary">
                On-call schedule <Avatar src={storeUser.avatar} size="small" /> {storeUser.username}
              </Text>
              {isOncall ? (
                <Badge text="On-call now" color="green" />
              ) : (
                /*  @ts-ignore */
                <Badge text="Not on-call now" color="gray" />
              )}
            </HorizontalGroup>
            <HorizontalGroup>
              <HorizontalGroup>
                <Text type="secondary">
                  {timezoneStore.calendarStartDate.format('DD MMM')} -{' '}
                  {timezoneStore.calendarStartDate.add(6, 'day').format('DD MMM')}
                </Text>
                <Button variant="secondary" size="sm" onClick={handleTodayClick}>
                  Today
                </Button>
                <HorizontalGroup spacing="xs">
                  <Button variant="secondary" size="sm" onClick={handleLeftClick}>
                    <Icon name="angle-left" />
                  </Button>
                  <Button variant="secondary" size="sm" onClick={handleRightClick}>
                    <Icon name="angle-right" />
                  </Button>
                </HorizontalGroup>
              </HorizontalGroup>
            </HorizontalGroup>
          </HorizontalGroup>
        </div>
      </div>
      <div className={cx('header-plus-content')}>
        {!currentTimeHidden && <div className={cx('current-time')} style={{ left: `${currentTimeX * 100}%` }} />}
        <TimelineMarks />
        <TransitionGroup className={cx('rotations')}>
          {shifts?.length ? (
            shifts.map(({ events }, index) => {
              return (
                <CSSTransition key={index} timeout={DEFAULT_TRANSITION_TIMEOUT} classNames={{ ...styles }}>
                  <Rotation
                    simplified
                    key={index}
                    events={events}
                    getColor={getColor}
                    onSlotClick={onSlotClick}
                    handleOpenSchedule={openSchedule}
                    showScheduleNameAsSlotTitle
                  />
                </CSSTransition>
              );
            })
          ) : (
            <CSSTransition key={0} timeout={DEFAULT_TRANSITION_TIMEOUT} classNames={{ ...styles }}>
              <Rotation events={[]} emptyText={emptyRotationsText} />
            </CSSTransition>
          )}
        </TransitionGroup>
      </div>
    </div>
  );
});

export const SchedulePersonal = withRouter(_SchedulePersonal);
