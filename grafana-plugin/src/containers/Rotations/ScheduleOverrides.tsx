import React, { Component } from 'react';

import { Button, HorizontalGroup, Icon, ValuePicker } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';

import TimelineMarks from 'components/TimelineMarks/TimelineMarks';
import Rotation from 'containers/Rotation/Rotation';
import { RotationCreateData } from 'containers/RotationForm/RotationForm.types';
import ScheduleOverrideForm from 'containers/RotationForm/ScheduleOverrideForm';
import { getFromString, getOverrideColor } from 'models/schedule/schedule.helpers';
import { Schedule, Shift } from 'models/schedule/schedule.types';
import { Timezone } from 'models/timezone/timezone.types';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';

import styles from './Rotations.module.css';

const cx = cn.bind(styles);

interface ScheduleOverridesProps extends WithStoreProps {
  startMoment: dayjs.Dayjs;
  currentTimezone: Timezone;
  scheduleId: Schedule['id'];
  onCreate: () => void;
  onUpdate: () => void;
}

interface ScheduleOverridesState {
  shiftIdToShowOverrideForm?: Shift['id'] | 'new';
}

@observer
class ScheduleOverrides extends Component<ScheduleOverridesProps, ScheduleOverridesState> {
  state: ScheduleOverridesState = {
    shiftIdToShowOverrideForm: undefined,
  };

  render() {
    const { scheduleId, startMoment, currentTimezone, onCreate, onUpdate, store } = this.props;
    const { shiftIdToShowOverrideForm } = this.state;

    const shifts = store.scheduleStore.events[scheduleId]?.['override']?.[getFromString(startMoment)];

    const base = 7 * 24 * 60; // in minutes
    const diff = dayjs().tz(currentTimezone).diff(startMoment, 'minutes');

    const currentTimeX = diff / base;

    const currentTimeHidden = currentTimeX < 0 || currentTimeX > 1;

    return (
      <>
        <div className={cx('root')}>
          <div className={cx('header')}>
            <HorizontalGroup justify="space-between">
              <div className={cx('title')}>Overrides</div>
              <Button icon="plus" onClick={this.handleAddOverride} variant="secondary">
                Add override
              </Button>
            </HorizontalGroup>
          </div>
          <div className={cx('header-plus-content')}>
            {!currentTimeHidden && <div className={cx('current-time')} style={{ left: `${currentTimeX * 100}%` }} />}
            <TimelineMarks startMoment={startMoment} />
            <div className={cx('rotations')}>
              {shifts && shifts.length ? (
                shifts.map(({ shiftId, events }, rotationIndex) => (
                  <Rotation
                    key={rotationIndex}
                    events={events}
                    color={getOverrideColor(rotationIndex)}
                    startMoment={startMoment}
                    currentTimezone={currentTimezone}
                    onClick={() => {
                      this.onRotationClick(shiftId);
                    }}
                  />
                ))
              ) : (
                <Rotation
                  events={[]}
                  startMoment={startMoment}
                  currentTimezone={currentTimezone}
                  onClick={() => {
                    this.onRotationClick('new');
                  }}
                />
              )}
            </div>
          </div>
          <div className={cx('add-rotations-layer')} onClick={this.handleAddOverride}>
            Add override +
          </div>
        </div>
        {shiftIdToShowOverrideForm && (
          <ScheduleOverrideForm
            shiftId={shiftIdToShowOverrideForm}
            scheduleId={scheduleId}
            currentTimezone={currentTimezone}
            onHide={() => {
              this.setState({ shiftIdToShowOverrideForm: undefined });
            }}
            onUpdate={onUpdate}
            onCreate={onCreate}
          />
        )}
      </>
    );
  }

  onRotationClick = (shiftId: Shift['id']) => {
    this.setState({ shiftIdToShowOverrideForm: shiftId });
  };

  handleAddOverride = () => {
    this.setState({ shiftIdToShowOverrideForm: 'new' });
  };
}

export default withMobXProviderContext(ScheduleOverrides);
