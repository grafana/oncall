import React, { Component } from 'react';

import { Badge, Button, HorizontalGroup, Icon } from '@grafana/ui';
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
import { Event } from 'models/schedule/schedule.types';
import { Timezone } from 'models/timezone/timezone.types';
import { User } from 'models/user/user.types';
import { getStartOfWeek } from 'pages/schedule/Schedule.helpers';
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

interface SchedulePersonalState {
  startMoment?: dayjs.Dayjs;
}

@observer
class SchedulePersonal extends Component<SchedulePersonalProps, SchedulePersonalState> {
  state: SchedulePersonalState = {};

  constructor(props) {
    super(props);

    this.state = {
      startMoment: props.startMoment,
    };
  }

  componentDidMount() {
    const { store } = this.props;
    const { startMoment } = this.state;

    store.scheduleStore.updatePersonalEvents(store.userStore.currentUserPk, startMoment, 9, true);
  }

  componentDidUpdate(prevProps: Readonly<SchedulePersonalProps>, prevState: Readonly<SchedulePersonalState>): void {
    const { store } = this.props;
    const { startMoment } = this.state;

    if (prevProps.currentTimezone !== this.props.currentTimezone) {
      const oldTimezone = prevProps.currentTimezone;

      this.setState((oldState) => {
        const wDiff = oldState.startMoment.diff(getStartOfWeek(oldTimezone), 'weeks');

        return { ...oldState, startMoment: getStartOfWeek(this.props.currentTimezone).add(wDiff, 'weeks') };
      });
    }

    if (prevState.startMoment !== startMoment) {
      store.scheduleStore.updatePersonalEvents(store.userStore.currentUserPk, startMoment);
    }
  }

  handleTodayClick = () => {
    const { store } = this.props;

    this.setState({ startMoment: getStartOfWeek(store.currentTimezone) });
  };

  handleLeftClick = () => {
    const { startMoment } = this.state;

    this.setState({ startMoment: startMoment.add(-7, 'day') });
  };

  handleRightClick = () => {
    const { startMoment } = this.state;

    this.setState({ startMoment: startMoment.add(7, 'day') });
  };

  render() {
    const { userPk, currentTimezone, store, onSlotClick } = this.props;
    const { startMoment } = this.state;

    const base = 7 * 24 * 60; // in minutes
    const diff = dayjs().tz(currentTimezone).diff(startMoment, 'minutes');

    const currentTimeX = diff / base;

    const shifts = getPersonalShiftsFromStore(store, userPk, startMoment);

    const currentTimeHidden = currentTimeX < 0 || currentTimeX > 1;

    const getColor = (event: Event) => getColorForSchedule(event.schedule?.id);

    const isOncall = store.scheduleStore.onCallNow[userPk];

    const storeUser = store.userStore.items[userPk];

    return (
      <>
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
                      {startMoment.format('DD MMM')} - {startMoment.add(6, 'day').format('DD MMM')}
                    </Text>
                    <Button variant="secondary" size="sm" onClick={this.handleTodayClick}>
                      Today
                    </Button>
                    <HorizontalGroup spacing="xs">
                      <Button variant="secondary" size="sm" onClick={this.handleLeftClick}>
                        <Icon name="angle-left" />
                      </Button>
                      <Button variant="secondary" size="sm" onClick={this.handleRightClick}>
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
