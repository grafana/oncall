import React, { Component } from 'react';

import { SelectableValue } from '@grafana/data';
import { ValuePicker, HorizontalGroup, Button, Tooltip } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';
import { CSSTransition, TransitionGroup } from 'react-transition-group';

import Text from 'components/Text/Text';
import TimelineMarks from 'components/TimelineMarks/TimelineMarks';
import Rotation from 'containers/Rotation/Rotation';
import RotationForm from 'containers/RotationForm/RotationForm';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { getColor, getFromString } from 'models/schedule/schedule.helpers';
import { Layer, Schedule, ScheduleType, Shift } from 'models/schedule/schedule.types';
import { Timezone } from 'models/timezone/timezone.types';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import { UserActions } from 'utils/authorization';

import { DEFAULT_TRANSITION_TIMEOUT } from './Rotations.config';
import { findColor } from './Rotations.helpers';

import styles from './Rotations.module.css';

const cx = cn.bind(styles);

interface RotationsProps extends WithStoreProps {
  startMoment: dayjs.Dayjs;
  currentTimezone: Timezone;
  shiftIdToShowRotationForm?: Shift['id'] | 'new';
  scheduleId: Schedule['id'];
  onShowRotationForm: (shiftId: Shift['id'] | 'new') => void;
  onClick: (id: Shift['id'] | 'new') => void;
  onCreate: () => void;
  onUpdate: () => void;
  onDelete: () => void;
  disabled: boolean;
}

interface RotationsState {
  layerPriority?: Layer['priority'];
  shiftMomentToShowRotationForm?: dayjs.Dayjs;
}

@observer
class Rotations extends Component<RotationsProps, RotationsState> {
  state: RotationsState = {
    layerPriority: undefined,
    shiftMomentToShowRotationForm: undefined,
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
    const { layerPriority, shiftMomentToShowRotationForm } = this.state;

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

    const schedule = store.scheduleStore.items[scheduleId];

    const isTypeReadOnly =
      schedule && (schedule?.type === ScheduleType.Ical || schedule?.type === ScheduleType.Calendar);

    return (
      <>
        <div className={cx('root')}>
          <div className={cx('header')}>
            <HorizontalGroup justify="space-between">
              <div className={cx('title')}>
                <Text.Title level={4} type="primary">
                  Rotations
                </Text.Title>
              </div>
              {disabled ? (
                isTypeReadOnly ? (
                  <Tooltip content="Ical and API/Terraform rotations are read-only here" placement="top">
                    <div>
                      <Button variant="primary" icon="plus" disabled>
                        Add rotation
                      </Button>
                    </div>
                  </Tooltip>
                ) : (
                  <WithPermissionControlTooltip userAction={UserActions.SchedulesWrite}>
                    <Button variant="primary" icon="plus" disabled>
                      Add rotation
                    </Button>
                  </WithPermissionControlTooltip>
                )
              ) : (
                <ValuePicker
                  label="Add rotation"
                  options={options}
                  onChange={this.handleAddRotation}
                  variant="primary"
                  size="md"
                />
              )}
            </HorizontalGroup>
          </div>
          <div className={cx('rotations-plus-title')}>
            {layers && layers.length ? (
              <TransitionGroup className={cx('layers')}>
                {layers.map((layer, layerIndex) => (
                  <CSSTransition key={layerIndex} timeout={DEFAULT_TRANSITION_TIMEOUT} classNames={{ ...styles }}>
                    <div id={`layer${layer.priority}`} className={cx('layer')}>
                      <div className={cx('layer-title')}>
                        <HorizontalGroup spacing="sm" justify="center">
                          <Text type="secondary">Layer {layer.priority}</Text>
                        </HorizontalGroup>
                      </div>
                      <div className={cx('rotations')}>
                        <TimelineMarks startMoment={startMoment} />
                        {!currentTimeHidden && (
                          <div className={cx('current-time')} style={{ left: `${currentTimeX * 100}%` }} />
                        )}
                        <TransitionGroup className={cx('rotations')}>
                          {layer.shifts.map(({ shiftId, isPreview, events }, rotationIndex) => (
                            <CSSTransition
                              key={rotationIndex}
                              timeout={DEFAULT_TRANSITION_TIMEOUT}
                              classNames={{ ...styles }}
                            >
                              <Rotation
                                scheduleId={scheduleId}
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
                                tutorialParams={isPreview && store.scheduleStore.rotationFormLiveParams}
                              />
                            </CSSTransition>
                          ))}
                        </TransitionGroup>
                      </div>
                    </div>
                  </CSSTransition>
                ))}
              </TransitionGroup>
            ) : (
              <div>
                <div id={`layer1`} className={cx('layer')}>
                  <div className={cx('layer-title')}>
                    <HorizontalGroup spacing="sm" justify="center">
                      <Text type="secondary">Layer 1</Text>
                    </HorizontalGroup>
                  </div>
                  <div className={cx('header-plus-content')}>
                    <div className={cx('current-time')} style={{ left: `${currentTimeX * 100}%` }} />
                    <TimelineMarks startMoment={startMoment} />
                    <div className={cx('rotations')}>
                      <Rotation
                        scheduleId={scheduleId}
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
                  if (disabled) {
                    return;
                  }
                  this.handleAddLayer(nextPriority, startMoment);
                }}
              >
                <Text type={disabled ? 'disabled' : 'primary'}>+ Add rotations layer</Text>
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
    const { disabled } = this.props;

    if (disabled) {
      return;
    }

    this.setState({ shiftMomentToShowRotationForm: moment }, () => {
      this.onShowRotationForm(shiftId);
    });
  };

  handleAddLayer = (layerPriority: number, moment?: dayjs.Dayjs) => {
    const { disabled } = this.props;

    if (disabled) {
      return;
    }

    this.setState({ layerPriority, shiftMomentToShowRotationForm: moment }, () => {
      this.onShowRotationForm('new');
    });
  };

  handleAddRotation = (option: SelectableValue) => {
    const { startMoment, disabled } = this.props;

    if (disabled) {
      return;
    }

    this.setState(
      {
        layerPriority: option.value,
        shiftMomentToShowRotationForm: startMoment,
      },
      () => {
        this.onShowRotationForm('new');
      }
    );
  };

  hideRotationForm = () => {
    this.setState(
      {
        layerPriority: undefined,
        shiftMomentToShowRotationForm: undefined,
      },
      () => {
        this.onShowRotationForm(undefined);
      }
    );
  };

  onShowRotationForm = (shiftId: Shift['id']) => {
    const { onShowRotationForm } = this.props;

    onShowRotationForm(shiftId);
  };
}

export default withMobXProviderContext(Rotations);
