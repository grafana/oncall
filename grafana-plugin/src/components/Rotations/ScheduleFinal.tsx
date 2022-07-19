import React, { Component } from 'react';

import { Button, HorizontalGroup, Icon, Input, ValuePicker } from '@grafana/ui';
import cn from 'classnames/bind';
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
    const { showAddOverrideForm, searchTerm } = this.state;

    return (
      <>
        <div className={cx('root')}>
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
          <div className={cx('header-plus-content')}>
            <div className={cx('current-time')} />
            <TimelineMarks startMoment={startMoment} />
            <div className={cx('rotations')}>
              <Rotation
                id="final"
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

export default withMobXProviderContext(ScheduleOverrides);
