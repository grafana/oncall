import React, { Component, useEffect } from 'react';

import { Button, HorizontalGroup, Icon, Input, ValuePicker } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { toJS } from 'mobx';
import { observer } from 'mobx-react';

import TimelineMarks from 'components/TimelineMarks/TimelineMarks';
import Rotation from 'containers/Rotation/Rotation';
import { getColor, getFromString } from 'models/schedule/schedule.helpers';
import { Layer, Schedule } from 'models/schedule/schedule.types';
import { Timezone } from 'models/timezone/timezone.types';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';

import styles from './Rotations.module.css';

const cx = cn.bind(styles);

interface ScheduleFinalProps extends WithStoreProps {
  startMoment: dayjs.Dayjs;
  currentTimezone: Timezone;
  scheduleId: Schedule['id'];
  hideHeader?: boolean;
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
      : store.scheduleStore.events[scheduleId]?.['final']?.[getFromString(startMoment)];

    const layers = store.scheduleStore.rotationPreview
      ? store.scheduleStore.rotationPreview
      : (store.scheduleStore.events[scheduleId]?.['rotation']?.[getFromString(startMoment)] as Layer[]);

    const currentTimeHidden = currentTimeX < 0 || currentTimeX > 1;

    /* console.log('shifts', toJS(shifts));
    console.log('layers', toJS(layers)); */

    return (
      <>
        <div className={cx('root')}>
          {!hideHeader && (
            <div className={cx('header')}>
              <HorizontalGroup justify="space-between">
                <div className={cx('title')}>Final schedule</div>
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
            <div className={cx('rotations')}>
              {shifts && shifts.length ? (
                shifts.map(({ shiftId, events }, index) => {
                  const layerIndex = layers
                    ? layers.findIndex((layer) => layer.shifts.some((shift) => shift.shiftId === shiftId))
                    : -1;

                  const rotationIndex =
                    layerIndex > -1 ? layers[layerIndex].shifts.findIndex((shift) => shift.shiftId === shiftId) : -1;

                  console.log(layerIndex, rotationIndex);

                  return (
                    <Rotation
                      key={index}
                      events={events}
                      startMoment={startMoment}
                      currentTimezone={currentTimezone}
                      color={getColor(layerIndex, rotationIndex)}
                    />
                  );
                })
              ) : (
                <Rotation events={[]} startMoment={startMoment} currentTimezone={currentTimezone} />
              )}
            </div>
          </div>
        </div>
      </>
    );
  }

  onSearchTermChangeCallback = () => {};
}

export default withMobXProviderContext(ScheduleFinal);
