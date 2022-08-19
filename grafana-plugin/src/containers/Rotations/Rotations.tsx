import React, { Component, useMemo, useState } from 'react';

import { ValuePicker, IconButton, Icon, HorizontalGroup, Button, LoadingPlaceholder } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';
import { toJS } from 'mobx';
import { observer } from 'mobx-react';

import TimelineMarks from 'components/TimelineMarks/TimelineMarks';
import Rotation from 'containers/Rotation/Rotation';
import RotationForm from 'containers/RotationForm/RotationForm';
import { RotationCreateData } from 'containers/RotationForm/RotationForm.types';
import { getColor, getFromString } from 'models/schedule/schedule.helpers';
import { Event, Layer, Schedule, Shift } from 'models/schedule/schedule.types';
import { Timezone } from 'models/timezone/timezone.types';
import { SelectOption, WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';

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
  layerPriority?: Layer['priority'];
}

@observer
class Rotations extends Component<RotationsProps, RotationsState> {
  state: RotationsState = {
    shiftIdToShowRotationForm: undefined,
  };

  render() {
    const { scheduleId, startMoment, currentTimezone, onCreate, onUpdate, store, onClick } = this.props;
    const { shiftIdToShowRotationForm, layerPriority } = this.state;

    const base = 7 * 24 * 60; // in minutes
    const diff = dayjs().tz(currentTimezone).diff(startMoment, 'minutes');

    const currentTimeX = diff / base;

    const currentTimeHidden = currentTimeX < 0 || currentTimeX > 1;

    const layers = store.scheduleStore.rotationPreview
      ? store.scheduleStore.rotationPreview
      : (store.scheduleStore.events[scheduleId]?.['rotation']?.[getFromString(startMoment)] as Layer[]);

    const options = layers
      ? layers.map((layer) => ({
          label: `Layer ${layer.priority}`,
          value: layer.priority,
        }))
      : [];

    const nextPriority = layers && layers.length ? layers[layers.length - 1].priority + 1 : 1;

    options.push({ label: 'New Layer', value: nextPriority });

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
              layers.map((layer, layerIndex) => (
                <div key={layer.priority}>
                  <div className={cx('layer')}>
                    <div className={cx('layer-title')}>
                      <HorizontalGroup spacing="sm" justify="center">
                        Layer {layer.priority} <Icon name="info-circle" />
                      </HorizontalGroup>
                    </div>
                    <div className={cx('rotations')}>
                      <TimelineMarks debug startMoment={startMoment} />
                      {!currentTimeHidden && (
                        <div className={cx('current-time')} style={{ left: `${currentTimeX * 100}%` }} />
                      )}
                      <div className={cx('rotations')}>
                        {layer.shifts.map(({ shiftId, events }, rotationIndex) => (
                          <Rotation
                            onClick={() => {
                              this.onRotationClick(shiftId);
                            }}
                            color={getColor(layerIndex, rotationIndex)}
                            events={events}
                            layerIndex={layerIndex}
                            rotationIndex={rotationIndex}
                            startMoment={startMoment}
                            currentTimezone={currentTimezone}
                          />
                        ))}
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
                          this.handleAddLayer(nextPriority);
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
                this.handleAddLayer(nextPriority);
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
            layerPriority={layerPriority}
            startMoment={startMoment}
            currentTimezone={currentTimezone}
            onHide={this.handleRotationFormHide}
            onUpdate={onUpdate}
            onCreate={onCreate}
          />
        )}
      </>
    );
  }

  handleRotationFormHide = () => {
    const { store } = this.props;

    store.scheduleStore.rotationPreview = undefined;
    store.scheduleStore.finalPreview = undefined;

    this.setState({ shiftIdToShowRotationForm: undefined, layerPriority: undefined });
  };

  onRotationClick = (shiftId: Shift['id']) => {
    this.setState({ shiftIdToShowRotationForm: shiftId });
  };

  handleAddLayer = (layerPriority: number) => {
    this.setState({ shiftIdToShowRotationForm: 'new', layerPriority });
  };

  handleAddRotation = (option: SelectOption) => {
    this.setState({ shiftIdToShowRotationForm: 'new', layerPriority: option.value });
  };
}

export default withMobXProviderContext(Rotations);
