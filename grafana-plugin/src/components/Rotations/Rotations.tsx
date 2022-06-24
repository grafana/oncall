import React, { Component, useMemo, useState } from 'react';

import { ValuePicker, IconButton, Icon, HorizontalGroup, Button } from '@grafana/ui';
import cn from 'classnames/bind';
import * as dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';

import Rotation from 'components/Rotation/Rotation';
import RotationForm from 'components/RotationForm/RotationForm';
import ScheduleTimeline from 'components/ScheduleTimeline/ScheduleTimeline';
import TimelineMarks from 'components/TimelineMarks/TimelineMarks';

import { getColor, getLabel, getRandomTimeslots, getRandomUser } from './Rotations.helpers';

import styles from './Rotations.module.css';

const cx = cn.bind(styles);

interface RotationsProps {
  title: string;
  startMoment: dayjs.Dayjs;
}

type Layer = {
  id: string;
};

interface RotationsState {
  layerIdToCreateRotation?: Layer['id'];
}

class Rotations extends Component<RotationsProps, RotationsState> {
  state: RotationsState = {
    //layerIdToCreateRotation: '12',
  };

  render() {
    const { title, startMoment } = this.props;
    const { layerIdToCreateRotation } = this.state;

    const layers = [
      { id: 0, title: 'Layer 1' },
      { id: 1, title: 'Layer 2' },
      { id: 2, title: 'Layer 3' },
      { id: 3, title: 'Layer 4' },
    ];

    const rotations = [{}, {}];

    return (
      <>
        <div className={cx('root')}>
          <div className={cx('header')}>
            <HorizontalGroup justify="space-between">
              <div className={cx('title')}>{title}</div>
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
            {layers.map((layer, layerIndex) => (
              <div key={layerIndex}>
                <div className={cx('layer')}>
                  <div className={cx('layer-title')}>
                    <HorizontalGroup spacing="sm" justify="center">
                      Layer {layerIndex + 1} <Icon name="info-circle" />
                    </HorizontalGroup>
                  </div>
                  <div className={cx('header-plus-content')}>
                    <div className={cx('current-time')} />
                    <TimelineMarks startMoment={startMoment} />
                    <div className={cx('rotations')}>
                      {rotations.map((rotation, rotationIndex) => (
                        <ScheduleTimeline
                          layerIndex={layerIndex}
                          rotationIndex={rotationIndex}
                          slots={getRandomTimeslots(6, layerIndex, rotationIndex)}
                          label={getLabel(layerIndex, rotationIndex)}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ))}
            <div className={cx('add-rotations-layer')}>Add rotations layer +</div>
          </div>
        </div>
        {layerIdToCreateRotation && (
          <RotationForm
            layerId={layerIdToCreateRotation}
            onHide={() => {
              this.setState({ layerIdToCreateRotation: undefined });
            }}
          />
        )}
      </>
    );
  }

  handleAddRotation = (option) => {
    this.setState({ layerIdToCreateRotation: option.value });
  };
}

export default Rotations;
