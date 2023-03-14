import React, { Component } from 'react';

import { Button, HorizontalGroup, Tooltip } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';
import { CSSTransition, TransitionGroup } from 'react-transition-group';

import Text from 'components/Text/Text';
import TimelineMarks from 'components/TimelineMarks/TimelineMarks';
import Rotation from 'containers/Rotation/Rotation';
import ScheduleOverrideForm from 'containers/RotationForm/ScheduleOverrideForm';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { getOverrideColor, getOverridesFromStore } from 'models/schedule/schedule.helpers';
import { Schedule, Shift, ShiftEvents } from 'models/schedule/schedule.types';
import { Timezone } from 'models/timezone/timezone.types';
import { getStartOfDay } from 'pages/schedule/Schedule.helpers';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import { UserActions } from 'utils/authorization';

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
  disabled: boolean;
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
    const {
      scheduleId,
      startMoment,
      currentTimezone,
      onCreate,
      onUpdate,
      onDelete,
      store,
      shiftIdToShowRotationForm,
      disabled,
    } = this.props;
    const { shiftMomentToShowOverrideForm } = this.state;

    const shifts = getOverridesFromStore(store, scheduleId, startMoment) as ShiftEvents[];

    const base = 7 * 24 * 60; // in minutes
    const diff = dayjs().tz(currentTimezone).diff(startMoment, 'minutes');

    const currentTimeX = diff / base;

    const currentTimeHidden = currentTimeX < 0 || currentTimeX > 1;

    const schedule = store.scheduleStore.items[scheduleId];

    const isTypeReadOnly = !schedule?.enable_web_overrides;

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
              {isTypeReadOnly ? (
                <Tooltip content="You can set an override using the override calendar" placement="top">
                  <div>
                    <Button variant="primary" icon="plus" disabled>
                      Add override
                    </Button>
                  </div>
                </Tooltip>
              ) : (
                <WithPermissionControlTooltip userAction={UserActions.SchedulesWrite}>
                  <Button disabled={disabled} icon="plus" onClick={this.handleAddOverride} variant="secondary">
                    Add override
                  </Button>
                </WithPermissionControlTooltip>
              )}
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
    const { disabled } = this.props;

    if (disabled) {
      return;
    }

    this.setState({ shiftMomentToShowOverrideForm: moment }, () => {
      this.onShowRotationForm(shiftId);
    });
  };

  handleAddOverride = () => {
    const { store, disabled } = this.props;

    if (disabled) {
      return;
    }

    // use start of current day as default start time for override
    const startMoment = getStartOfDay(store.currentTimezone);

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
