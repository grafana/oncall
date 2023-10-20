import React, { Component } from 'react';

import { Badge, HorizontalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';
import { RouteComponentProps, withRouter } from 'react-router-dom';
import { CSSTransition, TransitionGroup } from 'react-transition-group';

import Avatar from 'components/Avatar/Avatar';
import Text from 'components/Text/Text';
import TimelineMarks from 'components/TimelineMarks/TimelineMarks';
import Rotation from 'containers/Rotation/Rotation';
import { getColorForSchedule, getPersonalShiftsFromStore } from 'models/schedule/schedule.helpers';
import { Shift, Event } from 'models/schedule/schedule.types';
import { Timezone } from 'models/timezone/timezone.types';
import { User } from 'models/user/user.types';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import { PLUGIN_ROOT } from 'utils/consts';

import { DEFAULT_TRANSITION_TIMEOUT } from './Rotations.config';

import styles from './Rotations.module.css';

const cx = cn.bind(styles);

interface SchedulePersonalProps extends WithStoreProps, RouteComponentProps {
  startMoment: dayjs.Dayjs;
  currentTimezone: Timezone;
  userPk: User['pk'];
  onSlotClick?: (event: Event) => void;
}

@observer
class SchedulePersonal extends Component<SchedulePersonalProps> {
  componentDidMount() {
    const { store, startMoment } = this.props;

    store.scheduleStore.updatePersonalEvents(store.userStore.currentUserPk, startMoment);
  }

  componentDidUpdate(prevProps: Readonly<SchedulePersonalProps>): void {
    const { store, startMoment } = this.props;

    if (prevProps.startMoment !== this.props.startMoment) {
      store.scheduleStore.updatePersonalEvents(store.userStore.currentUserPk, startMoment);
    }
  }

  render() {
    const { userPk, startMoment, currentTimezone, store, onSlotClick } = this.props;

    const base = 7 * 24 * 60; // in minutes
    const diff = dayjs().tz(currentTimezone).diff(startMoment, 'minutes');

    const currentTimeX = diff / base;

    const shifts = getPersonalShiftsFromStore(store, userPk, startMoment);

    const currentTimeHidden = currentTimeX < 0 || currentTimeX > 1;

    const getColor = (shiftId: Shift['id']) => {
      const shift = store.scheduleStore.shifts[shiftId];

      if (!shift) {
        if (shiftId) {
          store.scheduleStore.updateOncallShift(shiftId);
        }
        return;
      }

      return getColorForSchedule(shift.schedule);
    };

    const isOncall = store.scheduleStore.onCallNow[userPk];

    const storeUser = store.userStore.items[userPk];

    return (
      <>
        <div className={cx('root')}>
          <div className={cx('header')}>
            <div className={cx('title')}>
              <HorizontalGroup>
                <Text type="secondary">
                  On-call schedule <Avatar src={storeUser.avatar} size="small" /> {store.userStore.currentUser.name}
                </Text>
                {/*  @ts-ignore */}
                {isOncall ? <Badge text="On-call now" color="green" /> : <Badge text="Not on-call now" color="gray" />}
              </HorizontalGroup>
            </div>
          </div>
          <div className={cx('header-plus-content')}>
            {!currentTimeHidden && <div className={cx('current-time')} style={{ left: `${currentTimeX * 100}%` }} />}
            <TimelineMarks startMoment={startMoment} timezone={currentTimezone} />
            <TransitionGroup className={cx('rotations')}>
              {shifts && shifts.length ? (
                shifts.map(({ events }, index) => {
                  return (
                    <CSSTransition key={index} timeout={DEFAULT_TRANSITION_TIMEOUT} classNames={{ ...styles }}>
                      <Rotation
                        simplified
                        key={index}
                        events={events}
                        startMoment={startMoment}
                        currentTimezone={currentTimezone}
                        getColor={getColor}
                        onSlotClick={onSlotClick}
                        handleOpenSchedule={this.openSchedule}
                        showScheduleNameAsSlotTitle
                      />
                    </CSSTransition>
                  );
                })
              ) : (
                <CSSTransition key={0} timeout={DEFAULT_TRANSITION_TIMEOUT} classNames={{ ...styles }}>
                  <Rotation
                    events={[]}
                    startMoment={startMoment}
                    currentTimezone={currentTimezone}
                    emptyText="There are no schedules relevant to user"
                  />
                </CSSTransition>
              )}
            </TransitionGroup>
          </div>
        </div>
      </>
    );
  }

  openSchedule = (event: Event) => {
    const { history } = this.props;

    history.push(`${PLUGIN_ROOT}/schedules/${event.schedule?.id}`);
  };
}

export default withRouter(withMobXProviderContext(SchedulePersonal));
