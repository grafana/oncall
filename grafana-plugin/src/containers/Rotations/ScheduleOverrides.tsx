import React, { Component } from 'react';

import { Button, HorizontalGroup, Icon, ValuePicker } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';
import { CSSTransition, TransitionGroup } from 'react-transition-group';

import Text from 'components/Text/Text';
import TimelineMarks from 'components/TimelineMarks/TimelineMarks';
import Rotation from 'containers/Rotation/Rotation';
import { RotationCreateData } from 'containers/RotationForm/RotationForm.types';
import ScheduleOverrideForm from 'containers/RotationForm/ScheduleOverrideForm';
import { getFromString, getOverrideColor } from 'models/schedule/schedule.helpers';
import { Event, Schedule, Shift } from 'models/schedule/schedule.types';
import { Timezone } from 'models/timezone/timezone.types';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';

import { DEFAULT_TRANSITION_TIMEOUT } from './Rotations.config';
import { findColor } from './Rotations.helpers';

import styles from './Rotations.module.css';

const cx = cn.bind(styles);

interface ScheduleOverridesProps extends WithStoreProps {
  startMoment: dayjs.Dayjs;
  currentTimezone: Timezone;
  scheduleId: Schedule['id'];
  shiftIdToShowRotationForm?: Shift['id'] | 'new';
  onShowRotationForm: (shiftId: Shift['id'] | 'new') => void;
  onCreate: () => void;
  onUpdate: () => void;
  onDelete: () => void;
}

interface ScheduleOverridesState {
  shiftMomentToShowOverrideForm?: dayjs.Dayjs;
}

@observer
class ScheduleOverrides extends Component<ScheduleOverridesProps, ScheduleOverridesState> {
  state: ScheduleOverridesState = {
    shiftMomentToShowOverrideForm: undefined,
  };

  render() {
    const { scheduleId, startMoment, currentTimezone, onCreate, onUpdate, onDelete, store, shiftIdToShowRotationForm } =
      this.props;
    const { shiftMomentToShowOverrideForm } = this.state;

    const shifts = store.scheduleStore.overridePreview
      ? store.scheduleStore.overridePreview
      : (store.scheduleStore.events[scheduleId]?.['override']?.[getFromString(startMoment)] as Array<{
          shiftId: string;
          events: Event[];
          isPreview?: boolean;
        }>);

    const base = 7 * 24 * 60; // in minutes
    const diff = dayjs().tz(currentTimezone).diff(startMoment, 'minutes');

    const currentTimeX = diff / base;

    const currentTimeHidden = currentTimeX < 0 || currentTimeX > 1;

    return (
      <>
        <div id="overrides-list" className={cx('root')}>
          <div className={cx('header')}>
            <HorizontalGroup justify="space-between">
              <div className={cx('title')}>
                <Text.Title level={4} type="primary">
                  Overrides
                </Text.Title>
              </div>
              <Button icon="plus" onClick={this.handleAddOverride} variant="secondary">
                Add override
              </Button>
            </HorizontalGroup>
          </div>
          <div className={cx('header-plus-content')}>
            {!currentTimeHidden && <div className={cx('current-time')} style={{ left: `${currentTimeX * 100}%` }} />}
            <TimelineMarks startMoment={startMoment} />
            <TransitionGroup className={cx('rotations')}>
              {shifts && shifts.length ? (
                shifts.map(({ shiftId, isPreview, events }, rotationIndex) => (
                  <CSSTransition key={rotationIndex} timeout={DEFAULT_TRANSITION_TIMEOUT} classNames={{ ...styles }}>
                    <Rotation
                      key={rotationIndex}
                      scheduleId={scheduleId}
                      events={events}
                      color={getOverrideColor(rotationIndex)}
                      startMoment={startMoment}
                      currentTimezone={currentTimezone}
                      onClick={(moment) => {
                        this.onRotationClick(shiftId, moment);
                      }}
                      transparent={isPreview}
                    />
                  </CSSTransition>
                ))
              ) : (
                <CSSTransition key={0} timeout={DEFAULT_TRANSITION_TIMEOUT} classNames={{ ...styles }}>
                  <Rotation
                    events={[]}
                    scheduleId={scheduleId}
                    startMoment={startMoment}
                    currentTimezone={currentTimezone}
                    onClick={(moment) => {
                      this.onRotationClick('new', moment);
                    }}
                  />
                </CSSTransition>
              )}
            </TransitionGroup>
          </div>
          {/* <div className={cx('add-rotations-layer')} onClick={this.handleAddOverride}>
            + Add override
          </div>*/}
        </div>
        {shiftIdToShowRotationForm && (
          <ScheduleOverrideForm
            shiftId={shiftIdToShowRotationForm}
            shiftColor={findColor(shiftIdToShowRotationForm, undefined, shifts)}
            scheduleId={scheduleId}
            startMoment={startMoment}
            currentTimezone={currentTimezone}
            shiftMoment={shiftMomentToShowOverrideForm}
            onHide={() => {
              this.handleHide();

              store.scheduleStore.clearPreview();
            }}
            onUpdate={() => {
              this.handleHide();

              onUpdate();
            }}
            onCreate={() => {
              this.handleHide();

              onCreate();
            }}
            onDelete={() => {
              this.handleHide();

              onDelete();
            }}
          />
        )}
      </>
    );
  }

  onRotationClick = (shiftId: Shift['id'], moment: dayjs.Dayjs) => {
    this.setState({ shiftMomentToShowOverrideForm: moment }, () => {
      this.onShowRotationForm(shiftId);
    });
  };

  handleAddOverride = () => {
    const { startMoment } = this.props;

    this.setState({ shiftMomentToShowOverrideForm: startMoment }, () => {
      this.onShowRotationForm('new');
    });
  };

  handleHide = () => {
    this.setState({ shiftMomentToShowOverrideForm: undefined }, () => {
      this.onShowRotationForm(undefined);
    });
  };

  onShowRotationForm = (shiftId: Shift['id']) => {
    const { onShowRotationForm } = this.props;

    onShowRotationForm(shiftId);
  };
}

export default withMobXProviderContext(ScheduleOverrides);
