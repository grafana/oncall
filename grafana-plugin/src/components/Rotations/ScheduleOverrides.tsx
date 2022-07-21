import React, { Component } from 'react';

import { Button, HorizontalGroup, Icon, ValuePicker } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';

import RotationForm from 'components/RotationForm/RotationForm';
import ScheduleOverrideForm from 'components/ScheduleOverrideForm/ScheduleOverrideForm';
import TimelineMarks from 'components/TimelineMarks/TimelineMarks';
import Rotation from 'containers/Rotation/Rotation';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';

import styles from './Rotations.module.css';

const cx = cn.bind(styles);

interface ScheduleOverridesProps extends WithStoreProps {}

interface ScheduleOverridesState {}

@observer
class ScheduleOverrides extends Component<ScheduleOverridesProps, ScheduleOverridesState> {
  state: ScheduleOverridesState = {};

  render() {
    const { title, startMoment, currentTimezone } = this.props;
    const { showAddOverrideForm } = this.state;

    const base = 7 * 24 * 60; // in minutes
    const diff = dayjs().tz(currentTimezone).diff(startMoment, 'minutes');

    const currentTimeX = diff / base;

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
            <div className={cx('current-time')} style={{ left: `${currentTimeX * 100}%` }} />
            <TimelineMarks startMoment={startMoment} />
            <div className={cx('rotations')}>
              <Rotation id="override" color="#C69B06" startMoment={startMoment} currentTimezone={currentTimezone} />
            </div>
          </div>
          <div className={cx('add-rotations-layer')}>Add override +</div>
        </div>
        {showAddOverrideForm && (
          <ScheduleOverrideForm
            onHide={() => {
              this.setState({ showAddOverrideForm: false });
            }}
          />
        )}
      </>
    );
  }

  handleAddOverride = () => {
    this.setState({ showAddOverrideForm: true });
  };
}

export default withMobXProviderContext(ScheduleOverrides);
