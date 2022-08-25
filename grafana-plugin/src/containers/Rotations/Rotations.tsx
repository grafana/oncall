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

import { findColor } from './Rotations.helpers';

import styles from './Rotations.module.css';

const cx = cn.bind(styles);

interface RotationsProps extends WithStoreProps {
  startMoment: dayjs.Dayjs;
  currentTimezone: Timezone;
  scheduleId: Schedule['id'];
  onClick: (id: Shift['id'] | 'new') => void;
  onCreate: () => void;
  onUpdate: () => void;
  onDelete: () => void;
}

interface RotationsState {
  shiftIdToShowRotationForm?: Shift['id'];
  layerPriority?: Layer['priority'];
  shiftMomentToShowRotationForm?: dayjs.Dayjs;
}

@observer
class Rotations extends Component<RotationsProps, RotationsState> {
  state: RotationsState = {
    shiftIdToShowRotationForm: undefined,
    shiftMomentToShowRotationForm: undefined,
  };

  render() {
    const { scheduleId, startMoment, currentTimezone, onCreate, onUpdate, onDelete, store, onClick } = this.props;
    const { shiftIdToShowRotationForm, layerPriority, shiftMomentToShowRotationForm } = this.state;

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
                  <div id={`layer${layer.priority}`} className={cx('layer')}>
                    <div className={cx('layer-title')}>
                      <HorizontalGroup spacing="sm" justify="center">
                        <span>Layer {layer.priority}</span>
                        {/*<Icon name="info-circle" />*/}
                      </HorizontalGroup>
                    </div>
                    <div className={cx('rotations')}>
                      <TimelineMarks startMoment={startMoment} />
                      {!currentTimeHidden && (
                        <div className={cx('current-time')} style={{ left: `${currentTimeX * 100}%` }} />
                      )}
                      <div className={cx('rotations')}>
                        {layer.shifts.map(({ shiftId, isPreview, events }, rotationIndex) => (
                          <Rotation
                            onClick={(moment) => {
                              this.onRotationClick(shiftId, moment);
                            }}
                            color={getColor(layerIndex, rotationIndex)}
                            events={events}
                            layerIndex={layerIndex}
                            rotationIndex={rotationIndex}
                            startMoment={startMoment}
                            currentTimezone={currentTimezone}
                            transparent={isPreview}
                          />
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div>
                <div id={`layer1`} className={cx('layer')}>
                  <div className={cx('layer-title')}>
                    <HorizontalGroup spacing="sm" justify="center">
                      <span>Layer 1</span>
                      {/* <Icon name="info-circle" />*/}
                    </HorizontalGroup>
                  </div>
                  <div className={cx('header-plus-content')}>
                    <div className={cx('current-time')} style={{ left: `${currentTimeX * 100}%` }} />
                    <TimelineMarks startMoment={startMoment} />
                    <div className={cx('rotations')}>
                      <Rotation
                        onClick={(moment) => {
                          this.handleAddLayer(nextPriority, moment);
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
            {nextPriority > 1 && (
              <div
                className={cx('add-rotations-layer')}
                onClick={() => {
                  this.handleAddLayer(nextPriority);
                }}
              >
                + Add rotations layer
              </div>
            )}
          </div>
        </div>
        {shiftIdToShowRotationForm && (
          <RotationForm
            shiftId={shiftIdToShowRotationForm}
            shiftColor={findColor(shiftIdToShowRotationForm, layers)}
            scheduleId={scheduleId}
            layerPriority={layerPriority}
            startMoment={startMoment}
            currentTimezone={currentTimezone}
            shiftMoment={shiftMomentToShowRotationForm}
            onHide={() => {
              this.hideRotationForm();

              store.scheduleStore.clearPreview();
            }}
            onUpdate={() => {
              this.hideRotationForm();

              onUpdate();
            }}
            onCreate={() => {
              this.hideRotationForm();

              onCreate();
            }}
            onDelete={() => {
              this.hideRotationForm();

              onDelete();
            }}
          />
        )}
      </>
    );
  }

  onRotationClick = (shiftId: Shift['id'], moment?: dayjs.Dayjs) => {
    this.setState({ shiftIdToShowRotationForm: shiftId, shiftMomentToShowRotationForm: moment });
  };

  handleAddLayer = (layerPriority: number, moment?: dayjs.Dayjs) => {
    this.setState({ shiftIdToShowRotationForm: 'new', layerPriority, shiftMomentToShowRotationForm: moment });
  };

  handleAddRotation = (option: SelectOption) => {
    this.setState({ shiftIdToShowRotationForm: 'new', layerPriority: option.value });
  };

  hideRotationForm = () => {
    const { store } = this.props;

    this.setState({
      shiftIdToShowRotationForm: undefined,
      layerPriority: undefined,
      shiftMomentToShowRotationForm: undefined,
    });
  };
}

export default withMobXProviderContext(Rotations);
