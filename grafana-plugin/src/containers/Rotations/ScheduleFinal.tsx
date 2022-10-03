import React, { Component, useEffect } from 'react';

import { Button, HorizontalGroup, Icon, Input, ValuePicker } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';
import { CSSTransition, TransitionGroup } from 'react-transition-group';

import Text from 'components/Text/Text';
import TimelineMarks from 'components/TimelineMarks/TimelineMarks';
import Rotation from 'containers/Rotation/Rotation';
import { getColor, getFromString, getOverrideColor } from 'models/schedule/schedule.helpers';
import { Event, Layer, Schedule, Shift } from 'models/schedule/schedule.types';
import { Timezone } from 'models/timezone/timezone.types';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';

import { DEFAULT_TRANSITION_TIMEOUT } from './Rotations.config';
import { findColor } from './Rotations.helpers';

import styles from './Rotations.module.css';

const cx = cn.bind(styles);

interface ScheduleFinalProps extends WithStoreProps {
  startMoment: dayjs.Dayjs;
  currentTimezone: Timezone;
  scheduleId: Schedule['id'];
  hideHeader?: boolean;
  onClick: (shiftId: Shift['id']) => void;
}

interface ScheduleOverridesState {
  searchTerm: string;
}

@observer
class ScheduleFinal extends Component<ScheduleFinalProps, ScheduleOverridesState> {
  state: ScheduleOverridesState = {
    searchTerm: '',
  };

  render() {
    const { scheduleId, startMoment, currentTimezone, store, hideHeader } = this.props;
    const { searchTerm } = this.state;

    const base = 7 * 24 * 60; // in minutes
    const diff = dayjs().tz(currentTimezone).diff(startMoment, 'minutes');

    const currentTimeX = diff / base;

    const shifts = store.scheduleStore.finalPreview
      ? store.scheduleStore.finalPreview
      : (store.scheduleStore.events[scheduleId]?.['final']?.[getFromString(startMoment)] as Array<{
          shiftId: string;
          events: Event[];
        }>);

    const layers = store.scheduleStore.rotationPreview
      ? store.scheduleStore.rotationPreview
      : (store.scheduleStore.events[scheduleId]?.['rotation']?.[getFromString(startMoment)] as Layer[]);

    const overrides = store.scheduleStore.overridePreview
      ? store.scheduleStore.overridePreview
      : store.scheduleStore.events[scheduleId]?.['override']?.[getFromString(startMoment)];
    const currentTimeHidden = currentTimeX < 0 || currentTimeX > 1;

    /* console.log('shifts', toJS(shifts));
    console.log('layers', toJS(layers)); */

    return (
      <>
        <div className={cx('root')}>
          {!hideHeader && (
            <div className={cx('header')}>
              <HorizontalGroup justify="space-between">
                <div className={cx('title')}>
                  <Text.Title level={4} type="primary">
                    Final schedule
                  </Text.Title>
                </div>
                {/*<Input
                  prefix={<Icon name="search" />}
                  placeholder="Search..."
                  value={searchTerm}
                  onChange={this.onSearchTermChangeCallback}
                />*/}
              </HorizontalGroup>
            </div>
          )}
          <div className={cx('header-plus-content')}>
            {!currentTimeHidden && <div className={cx('current-time')} style={{ left: `${currentTimeX * 100}%` }} />}
            <TimelineMarks startMoment={startMoment} />
            <TransitionGroup className={cx('rotations')}>
              {shifts && shifts.length ? (
                shifts.map(({ shiftId, events }, index) => {
                  return (
                    <CSSTransition key={index} timeout={DEFAULT_TRANSITION_TIMEOUT} classNames={{ ...styles }}>
                      <Rotation
                        key={index}
                        scheduleId={scheduleId}
                        events={events}
                        startMoment={startMoment}
                        currentTimezone={currentTimezone}
                        color={findColor(shiftId, layers, overrides)}
                        onClick={this.getRotationClickHandler(shiftId)}
                      />
                    </CSSTransition>
                  );
                })
              ) : (
                <CSSTransition key={0} timeout={DEFAULT_TRANSITION_TIMEOUT} classNames={{ ...styles }}>
                  <Rotation
                    scheduleId={scheduleId}
                    events={[]}
                    startMoment={startMoment}
                    currentTimezone={currentTimezone}
                  />
                </CSSTransition>
              )}
            </TransitionGroup>
          </div>
        </div>
      </>
    );
  }

  getRotationClickHandler = (shiftId: Shift['id']) => {
    const { onClick } = this.props;

    return () => {
      onClick(shiftId);
    };
  };

  onSearchTermChangeCallback = () => {};
}

export default withMobXProviderContext(ScheduleFinal);
