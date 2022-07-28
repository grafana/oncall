import React, { Component, useMemo, useState } from 'react';

import { ValuePicker, IconButton, Icon, HorizontalGroup, Button, LoadingPlaceholder } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';
import { observer } from 'mobx-react';

import TimelineMarks from 'components/TimelineMarks/TimelineMarks';
import Rotation from 'containers/Rotation/Rotation';
import RotationForm from 'containers/RotationForm/RotationForm';
import { RotationCreateData } from 'containers/RotationForm/RotationForm.types';
import { getFromString } from 'models/schedule/schedule.helpers';
import { Schedule, Shift } from 'models/schedule/schedule.types';
import { Timezone } from 'models/timezone/timezone.types';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';

import { getColor, getLabel, getRandomTimeslots, getRandomUser } from './Rotations.helpers';

import styles from './Rotations.module.css';

const cx = cn.bind(styles);

interface RotationsProps extends WithStoreProps {
  startMoment: dayjs.Dayjs;
  currentTimezone: Timezone;
  scheduleId: Schedule['id'];
  onClick: (id: Shift['id'] | 'new') => void;
  onCreate: () => void;
  onUpdate: () => void;
}

type Layer = {
  id: string;
};

interface RotationsState {
  shiftIdToShowRotationForm?: Shift['id'];
}

@observer
class Rotations extends Component<RotationsProps, RotationsState> {
  state: RotationsState = {
    shiftIdToShowRotationForm: undefined,
  };

  render() {
    const { scheduleId, startMoment, currentTimezone, onCreate, onUpdate, store, onClick } = this.props;
    const { shiftIdToShowRotationForm } = this.state;

    const layers = [
      { id: 1, title: 'Layer 1' },
      /*{ id: 1, title: 'Layer 2' },
     { id: 2, title: 'Layer 3' },
      { id: 3, title: 'Layer 4' }*/
    ];

    const base = 7 * 24 * 60; // in minutes
    const diff = dayjs().tz(currentTimezone).diff(startMoment, 'minutes');

    const currentTimeX = diff / base;

    const rotations = [{} /* {}*/];

    const shifts = store.scheduleStore.events[scheduleId]?.['rotation']?.[getFromString(startMoment)];

    return (
      <>
        <div className={cx('root')}>
          <div className={cx('header')}>
            <HorizontalGroup justify="space-between">
              <div className={cx('title')}>Rotations</div>
              <ValuePicker
                label="Add rotation"
                options={layers.map(({ title, id }) => ({
                  label: title,
                  value: id,
                }))}
                onChange={this.handleAddRotation}
                variant="secondary"
                size="md"
              />
            </HorizontalGroup>
          </div>
          <div className={cx('rotations-plus-title')}>
            {shifts && shifts.length ? (
              shifts.map(({ shiftId, events }, layerIndex) => (
                <div key={layerIndex}>
                  <div className={cx('layer')}>
                    <div className={cx('layer-title')}>
                      <HorizontalGroup spacing="sm" justify="center">
                        Layer {layerIndex + 1} <Icon name="info-circle" />
                      </HorizontalGroup>
                    </div>
                    <div className={cx('header-plus-content')}>
                      <div className={cx('current-time')} style={{ left: `${currentTimeX * 100}%` }} />
                      <TimelineMarks debug startMoment={startMoment} />
                      <div className={cx('rotations')}>
                        <Rotation
                          onClick={() => {
                            this.onRotationClick(shiftId);
                          }}
                          events={events}
                          layerIndex={layerIndex}
                          rotationIndex={0}
                          startMoment={startMoment}
                          currentTimezone={currentTimezone}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div>
                <div className={cx('layer')}>
                  <div className={cx('layer-title')}>
                    <HorizontalGroup spacing="sm" justify="center">
                      Layer 1 <Icon name="info-circle" />
                    </HorizontalGroup>
                  </div>
                  <div className={cx('header-plus-content')}>
                    <div className={cx('current-time')} style={{ left: `${currentTimeX * 100}%` }} />
                    <TimelineMarks debug startMoment={startMoment} />
                    <div className={cx('rotations')}>
                      <Rotation
                        onClick={() => {
                          this.onRotationClick('new');
                        }}
                        events={[]}
                        layerIndex={0}
                        rotationIndex={0}
                        startMoment={startMoment}
                        currentTimezone={currentTimezone}
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div className={cx('add-rotations-layer')} onClick={this.handleAddLayer}>
              Add rotations layer +
            </div>
          </div>
        </div>
        {shiftIdToShowRotationForm && (
          <RotationForm
            shiftId={shiftIdToShowRotationForm}
            scheduleId={scheduleId}
            layerIndex={shifts ? shifts.length : 0}
            currentTimezone={currentTimezone}
            onHide={() => {
              this.setState({ shiftIdToShowRotationForm: undefined });
            }}
            onUpdate={onUpdate}
            onCreate={onCreate}
          />
        )}
      </>
    );
  }

  onRotationClick = (shiftId: Shift['id']) => {
    this.setState({ shiftIdToShowRotationForm: shiftId });
  };

  updateEvents = () => {};

  handleAddLayer = () => {};

  handleAddRotation = (option) => {
    this.setState({ shiftIdToShowRotationForm: option.value });
  };
}

export default withMobXProviderContext(Rotations);
