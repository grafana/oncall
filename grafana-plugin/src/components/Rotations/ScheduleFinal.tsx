import React, { Component, useEffect } from 'react';

import { Button, HorizontalGroup, Icon, Input, ValuePicker } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';

import RotationForm from 'components/RotationForm/RotationForm';
import ScheduleOverrideForm from 'components/ScheduleOverrideForm/ScheduleOverrideForm';
import TimelineMarks from 'components/TimelineMarks/TimelineMarks';
import Rotation from 'containers/Rotation/Rotation';
import { Schedule } from 'models/schedule/schedule.types';
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

interface ScheduleOverridesState {}

@observer
class ScheduleFinal extends Component<ScheduleFinalProps, ScheduleOverridesState> {
  state: ScheduleOverridesState = {};

  render() {
    const { scheduleId, startMoment, currentTimezone, store, hideHeader } = this.props;
    const { showAddOverrideForm, searchTerm } = this.state;

    const base = 7 * 24 * 60; // in minutes
    const diff = dayjs().tz(currentTimezone).diff(startMoment, 'minutes');

    const currentTimeX = diff / base;

    return (
      <>
        <div className={cx('root')}>
          {!hideHeader && (
            <div className={cx('header')}>
              <HorizontalGroup justify="space-between">
                <div className={cx('title')}>Final schedule</div>
                <Input
                  prefix={<Icon name="search" />}
                  placeholder="Search..."
                  value={searchTerm}
                  onChange={this.onSearchTermChangeCallback}
                />
              </HorizontalGroup>
            </div>
          )}
          <div className={cx('header-plus-content')}>
            <div className={cx('current-time')} style={{ left: `${currentTimeX * 100}%` }} />
            <TimelineMarks startMoment={startMoment} />
            <div className={cx('rotations')}>
              <Rotation
                type="final"
                scheduleId={scheduleId}
                startMoment={startMoment}
                currentTimezone={currentTimezone}
                layerIndex={0}
                rotationIndex={0}
              />
            </div>
          </div>
        </div>
      </>
    );
  }

  onSearchTermChangeCallback = () => {};
}

export default ScheduleFinal;
