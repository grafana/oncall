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
import { Event, Schedule, Shift } from 'models/schedule/schedule.types';
import { Timezone } from 'models/timezone/timezone.types';
import { SelectOption, WithStoreProps } from 'state/types';
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

interface RotationsState {
  shiftIdToShowRotationForm?: Shift['id'];
  layerIndexToShowRotationForm?: number;
}

interface Layer {
  priority: Shift['priority_level'];
  shifts: Array<{ shiftId: Shift['id']; events: Event[] }>;
}

@observer
class Rotations extends Component<RotationsProps, RotationsState> {
  state: RotationsState = {
    shiftIdToShowRotationForm: undefined,
  };

  render() {
    const { scheduleId, startMoment, currentTimezone, onCreate, onUpdate, store, onClick } = this.props;
    const { shiftIdToShowRotationForm, layerIndexToShowRotationForm } = this.state;

    const base = 7 * 24 * 60; // in minutes
    const diff = dayjs().tz(currentTimezone).diff(startMoment, 'minutes');

    const currentTimeX = diff / base;

    const currentTimeHidden = currentTimeX < 0 || currentTimeX > 1;

    const shifts = store.scheduleStore.events[scheduleId]?.['rotation']?.[getFromString(startMoment)];

    const layers: Layer[] | undefined = shifts
      ? shifts
          .reduce((memo, shift) => {
            const storeShift = store.scheduleStore.shifts[shift.shiftId];
            let layer = memo.find((level) => level.priority === storeShift.priority_level);
            if (!layer) {
              layer = { priority: storeShift.priority_level, shifts: [] };
              memo.push(layer);
            }
            layer.shifts.push(shift);

            return memo;
          }, [])
          .sort((a, b) => {
            if (a.priority > b.priority) {
              return 1;
            }
            if (a.priority < b.priority) {
              return -1;
            }

            return 0;
          })
      : undefined;

    const options = layers
      ? layers.map((layer) => ({
          label: `Layer ${layer.priority}`,
          value: layer.priority - 1,
        }))
      : [];

    options.push({ label: 'New Layer', value: layers?.length || 0 });

    return (
      <>
        <div className={cx('root')}>
          <div className={cx('header')}>
            <HorizontalGroup justify="space-between">
              <div className={cx('title')}>Rotations</div>
              <ValuePicker
                label="Add rotation"
                options={options}
                onChange={this.handleAddRotation}
                variant="secondary"
                size="md"
              />
            </HorizontalGroup>
          </div>
          <div className={cx('rotations-plus-title')}>
            {layers && layers.length ? (
              layers.map((layer) => (
                <div key={layer.priority}>
                  <div className={cx('layer')}>
                    <div className={cx('layer-title')}>
                      <HorizontalGroup spacing="sm" justify="center">
                        Layer {layer.priority} <Icon name="info-circle" />
                      </HorizontalGroup>
                    </div>
                    <div className={cx('rotations')}>
                      <TimelineMarks debug startMoment={startMoment} />
                      {layer.shifts.map(({ shiftId, events }, rotationIndex) => (
                        <div className={cx('header-plus-content')}>
                          {!currentTimeHidden && (
                            <div className={cx('current-time')} style={{ left: `${currentTimeX * 100}%` }} />
                          )}
                          <div>
                            <Rotation
                              onClick={() => {
                                this.onRotationClick(shiftId);
                              }}
                              events={events}
                              layerIndex={layer.priority - 1}
                              rotationIndex={rotationIndex}
                              startMoment={startMoment}
                              currentTimezone={currentTimezone}
                            />
                          </div>
                        </div>
                      ))}
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
                          this.handleAddLayer(layers ? layers.length : 0);
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

            <div
              className={cx('add-rotations-layer')}
              onClick={() => {
                this.handleAddLayer(layers ? layers.length : 0);
              }}
            >
              Add rotations layer +
            </div>
          </div>
        </div>
        {shiftIdToShowRotationForm && (
          <RotationForm
            shiftId={shiftIdToShowRotationForm}
            scheduleId={scheduleId}
            layerIndex={layerIndexToShowRotationForm}
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

  handleAddLayer = (layerIndex: number) => {
    this.setState({ shiftIdToShowRotationForm: 'new', layerIndexToShowRotationForm: layerIndex });
  };

  handleAddRotation = (option: SelectOption) => {
    this.setState({ shiftIdToShowRotationForm: 'new', layerIndexToShowRotationForm: option.value });
  };
}

export default withMobXProviderContext(Rotations);
