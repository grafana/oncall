import React, { Component } from 'react';

import { SelectableValue } from '@grafana/data';
import { ValuePicker, HorizontalGroup, Button, Tooltip } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';
import { CSSTransition, TransitionGroup } from 'react-transition-group';

import { ScheduleFiltersType } from 'components/ScheduleFilters/ScheduleFilters.types';
import Text from 'components/Text/Text';
import TimelineMarks from 'components/TimelineMarks/TimelineMarks';
import Rotation from 'containers/Rotation/Rotation';
import RotationForm from 'containers/RotationForm/RotationForm';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { getColor, getLayersFromStore } from 'models/schedule/schedule.helpers';
import { Layer, Schedule, ScheduleType, Shift, ShiftSwap, Event } from 'models/schedule/schedule.types';
import { Timezone } from 'models/timezone/timezone.types';
import { User } from 'models/user/user.types';
import { getUTCString } from 'pages/schedule/Schedule.helpers';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import { UserActions } from 'utils/authorization';

import { DEFAULT_TRANSITION_TIMEOUT } from './Rotations.config';
import { findClosestUserEvent, findColor } from './Rotations.helpers';

import styles from './Rotations.module.css';

const cx = cn.bind(styles);

interface RotationsProps extends WithStoreProps {
  startMoment: dayjs.Dayjs;
  currentTimezone: Timezone;
  shiftIdToShowRotationForm?: Shift['id'] | 'new';
  scheduleId: Schedule['id'];
  onShowRotationForm: (shiftId: Shift['id'] | 'new') => void;
  onClick: (id: Shift['id'] | 'new') => void;
  onShowOverrideForm: (shiftId: 'new', shiftStart: dayjs.Dayjs, shiftEnd: dayjs.Dayjs) => void;
  onShowShiftSwapForm: (id: ShiftSwap['id'] | 'new', params?: Partial<ShiftSwap>) => void;
  onCreate: () => void;
  onUpdate: () => void;
  onDelete: () => void;
  onShiftSwapRequest: (beneficiary: User['pk'], swap_start: string, swap_end: string) => void;
  disabled: boolean;
  filters: ScheduleFiltersType;
  onSlotClick?: (event: Event) => void;
}

interface RotationsState {
  layerPriority?: Layer['priority'];
  shiftStartToShowRotationForm?: dayjs.Dayjs;
  shiftEndToShowRotationForm?: dayjs.Dayjs;
}

@observer
class Rotations extends Component<RotationsProps, RotationsState> {
  state: RotationsState = {
    layerPriority: undefined,
    shiftStartToShowRotationForm: undefined,
    shiftEndToShowRotationForm: undefined,
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
      filters,
      onShowShiftSwapForm,
      onSlotClick,
      store: {
        userStore: { currentUserPk },
      },
    } = this.props;
    const { layerPriority, shiftStartToShowRotationForm, shiftEndToShowRotationForm } = this.state;

    const base = 7 * 24 * 60; // in minutes
    const diff = dayjs().tz(currentTimezone).diff(startMoment, 'minutes');

    const currentTimeX = diff / base;

    const currentTimeHidden = currentTimeX < 0 || currentTimeX > 1;

    const layers = getLayersFromStore(store, scheduleId, startMoment);

    const options = layers
      ? layers.map((layer) => ({
          label: `Layer ${layer.priority} rotation`,
          value: layer.priority,
        }))
      : [];

    const nextPriority = layers && layers.length ? layers[layers.length - 1].priority + 1 : 1;

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
              <HorizontalGroup>
                <Button
                  variant="secondary"
                  onClick={() => {
                    const closestEvent = findClosestUserEvent(dayjs(), currentUserPk, layers);
                    const swapStart = closestEvent
                      ? dayjs(closestEvent.start)
                      : dayjs().tz(currentTimezone).startOf('day').add(1, 'day');

                    const swapEnd = closestEvent ? dayjs(closestEvent.end) : swapStart.add(1, 'day');

                    onShowShiftSwapForm('new', {
                      swap_start: getUTCString(swapStart),
                      swap_end: getUTCString(swapEnd),
                    });
                  }}
                >
                  Request shift swap
                </Button>
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
                ) : options.length > 0 ? (
                  <ValuePicker
                    label="Add rotation"
                    options={options}
                    onChange={this.handleAddRotation}
                    variant="primary"
                    size="md"
                  />
                ) : (
                  <Button variant="primary" icon="plus" onClick={() => this.handleAddLayer(nextPriority, startMoment)}>
                    Add rotation
                  </Button>
                )}
              </HorizontalGroup>
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
                        <TimelineMarks startMoment={startMoment} timezone={currentTimezone} />
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
                                onClick={(shiftStart, shiftEnd) => {
                                  this.onRotationClick(shiftId, shiftStart, shiftEnd);
                                }}
                                handleAddOverride={this.handleShowOverrideForm}
                                handleAddShiftSwap={onShowShiftSwapForm}
                                onShiftSwapClick={onShowShiftSwapForm}
                                color={getColor(layerIndex, rotationIndex)}
                                events={events}
                                layerIndex={layerIndex}
                                rotationIndex={rotationIndex}
                                startMoment={startMoment}
                                currentTimezone={currentTimezone}
                                transparent={isPreview}
                                tutorialParams={isPreview && store.scheduleStore.rotationFormLiveParams}
                                filters={filters}
                                onSlotClick={onSlotClick}
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
                    <TimelineMarks startMoment={startMoment} timezone={currentTimezone} />
                    <div className={cx('rotations')}>
                      <Rotation
                        scheduleId={scheduleId}
                        onClick={(shiftStart, shiftEnd) => {
                          this.handleAddLayer(nextPriority, shiftStart, shiftEnd);
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
                <Text type={disabled ? 'disabled' : 'primary'}>+ Add new layer with rotation</Text>
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
            shiftStart={shiftStartToShowRotationForm}
            shiftEnd={shiftEndToShowRotationForm}
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
            onShowRotationForm={this.onShowRotationForm}
          />
        )}
      </>
    );
  }

  onRotationClick = (shiftId: Shift['id'], shiftStart: dayjs.Dayjs, shiftEnd: dayjs.Dayjs) => {
    const { disabled } = this.props;

    if (disabled) {
      return;
    }

    this.setState({ shiftStartToShowRotationForm: shiftStart, shiftEndToShowRotationForm: shiftEnd }, () => {
      this.onShowRotationForm(shiftId);
    });
  };

  handleAddLayer = (layerPriority: number, shiftStart?: dayjs.Dayjs, shiftEnd?: dayjs.Dayjs) => {
    const { disabled } = this.props;

    if (disabled) {
      return;
    }

    this.setState(
      { layerPriority, shiftStartToShowRotationForm: shiftStart, shiftEndToShowRotationForm: shiftEnd },
      () => {
        this.onShowRotationForm('new');
      }
    );
  };

  handleAddRotation = (option: SelectableValue) => {
    const { startMoment, disabled } = this.props;

    if (disabled) {
      return;
    }

    this.setState(
      {
        layerPriority: option.value,
        shiftStartToShowRotationForm: startMoment,
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
        shiftStartToShowRotationForm: undefined,
        shiftEndToShowRotationForm: undefined,
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

  handleShowOverrideForm = (shiftStart: dayjs.Dayjs, shiftEnd: dayjs.Dayjs) => {
    const { onShowOverrideForm } = this.props;

    onShowOverrideForm('new', shiftStart, shiftEnd);
  };
}

export default withMobXProviderContext(Rotations);
