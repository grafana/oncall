import React, { FC, useEffect } from 'react';

import { cx } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { Badge, BadgeColor, Button, HorizontalGroup, Icon, useStyles2, withTheme2 } from '@grafana/ui';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';
import { RouteComponentProps, withRouter } from 'react-router-dom';
import { CSSTransition, TransitionGroup } from 'react-transition-group';

import { Avatar } from 'components/Avatar/Avatar';
import { RenderConditionally } from 'components/RenderConditionally/RenderConditionally';
import { Text } from 'components/Text/Text';
import { Rotation } from 'containers/Rotation/Rotation';
import { TimelineMarks } from 'containers/TimelineMarks/TimelineMarks';
import { ActionKey } from 'models/loader/action-keys';
import {
  getColorForSchedule,
  getPersonalShiftsFromStore,
  getTotalDaysToDisplay,
  scheduleViewToDaysInOneRow,
} from 'models/schedule/schedule.helpers';
import { Event, ScheduleView } from 'models/schedule/schedule.types';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { getCurrentTimeX, getStartOfWeekBasedOnCurrentDate } from 'pages/schedule/Schedule.helpers';
import { useStore } from 'state/useStore';
import { PLUGIN_ROOT } from 'utils/consts';
import { useIsLoading } from 'utils/hooks';

import { DEFAULT_TRANSITION_TIMEOUT } from './Rotations.config';
import { getRotationsStyles } from './Rotations.styles';

import animationStyles from './Rotations.module.css';

interface SchedulePersonalProps extends RouteComponentProps {
  userPk: ApiSchemas['User']['pk'];
  onSlotClick?: (event: Event) => void;
  theme: GrafanaTheme2;
}

const _SchedulePersonal: FC<SchedulePersonalProps> = observer(({ userPk, onSlotClick, history }) => {
  const store = useStore();
  const { timezoneStore, scheduleStore, userStore } = store;
  const updatePersonalEventsLoading = useIsLoading(ActionKey.UPDATE_PERSONAL_EVENTS);

  useEffect(() => {
    updatePersonalEvents();
  }, [timezoneStore.selectedTimezoneOffset]);

  const updatePersonalEvents = () => {
    scheduleStore.updatePersonalEvents(userStore.currentUserPk, timezoneStore.calendarStartDate, true);
  };

  const handleTodayClick = () => {
    // TODAY
    timezoneStore.setCalendarStartDate(getStartOfWeekBasedOnCurrentDate(dayjs()));
  };

  const handleLeftClick = () => {
    timezoneStore.setCalendarStartDate(
      timezoneStore.calendarStartDate.subtract(
        getTotalDaysToDisplay(ScheduleView.OneWeek, store.timezoneStore.calendarStartDate),
        'day'
      )
    );
    scheduleStore.updatePersonalEvents(userStore.currentUserPk, timezoneStore.calendarStartDate);
  };

  const handleRightClick = () => {
    timezoneStore.setCalendarStartDate(
      timezoneStore.calendarStartDate.add(
        getTotalDaysToDisplay(ScheduleView.OneWeek, store.timezoneStore.calendarStartDate),
        'day'
      )
    );
    scheduleStore.updatePersonalEvents(userStore.currentUserPk, timezoneStore.calendarStartDate);
  };

  const openSchedule = (event: Event) => {
    history.push(`${PLUGIN_ROOT}/schedules/${event.schedule?.id}`);
  };

  const currentTimeX = getCurrentTimeX(
    timezoneStore.currentDateInSelectedTimezone,
    timezoneStore.calendarStartDate,
    scheduleViewToDaysInOneRow[ScheduleView.OneWeek] * 24 * 60
  );

  const shifts = getPersonalShiftsFromStore(store, userPk, timezoneStore.calendarStartDate);

  const currentTimeHidden = currentTimeX < 0 || currentTimeX > 1;

  const getColor = (event: Event) => getColorForSchedule(event.schedule?.id);

  const isOncall = scheduleStore.onCallNow[userPk];

  const storeUser = userStore.items[userPk];

  const emptyRotationsText = updatePersonalEventsLoading ? 'Loading ...' : 'There are no schedules relevant to user';

  const styles = useStyles2(getRotationsStyles);

  return (
    <div className={styles.root}>
      <div className={styles.header}>
        <HorizontalGroup justify="space-between">
          <HorizontalGroup>
            <RenderConditionally
              shouldRender={Boolean(storeUser)}
              render={() => (
                <Text type="secondary">
                  On-call schedule <Avatar src={storeUser.avatar} size="small" /> {storeUser.username}
                </Text>
              )}
            />
            {isOncall ? (
              <Badge text="On-call now" color="green" />
            ) : (
              <Badge text="Not on-call now" color={'gray' as BadgeColor} />
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
      <div className={'u-position-relative'}>
        {!currentTimeHidden && <div className={styles.currentTime} style={{ left: `${currentTimeX * 100}%` }} />}
        <TimelineMarks scheduleView={ScheduleView.OneWeek} />
        <TransitionGroup className={cx(styles.layer, styles.layerFirst)}>
          {shifts?.length ? (
            shifts.map(({ events }, index) => {
              return (
                <CSSTransition key={index} timeout={DEFAULT_TRANSITION_TIMEOUT} classNames={{ ...animationStyles }}>
                  <Rotation
                    scheduleView={ScheduleView.OneWeek}
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
            <CSSTransition key={0} timeout={DEFAULT_TRANSITION_TIMEOUT} classNames={{ ...animationStyles }}>
              <Rotation events={[]} emptyText={emptyRotationsText} />
            </CSSTransition>
          )}
        </TransitionGroup>
      </div>
    </div>
  );
});

export const SchedulePersonal = withRouter(withTheme2(_SchedulePersonal));
