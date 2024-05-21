import React, { Component } from 'react';

import { cx } from '@emotion/css';
import { GrafanaTheme2, SelectableValue } from '@grafana/data';
import { ValuePicker, HorizontalGroup, Button, Tooltip, withTheme2 } from '@grafana/ui';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';
import { CSSTransition, TransitionGroup } from 'react-transition-group';

import { ScheduleFiltersType } from 'components/ScheduleFilters/ScheduleFilters.types';
import { Text } from 'components/Text/Text';
import { Rotation } from 'containers/Rotation/Rotation';
import { RotationForm } from 'containers/RotationForm/RotationForm';
import { TimelineMarks } from 'containers/TimelineMarks/TimelineMarks';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { getColor, getLayersFromStore } from 'models/schedule/schedule.helpers';
import { Layer, Schedule, ScheduleType, Shift, ShiftSwap, Event } from 'models/schedule/schedule.types';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import { UserActions } from 'utils/authorization/authorization';

import { DEFAULT_TRANSITION_TIMEOUT } from './Rotations.config';
import { findColor } from './Rotations.helpers';
import { getRotationsStyles } from './Rotations.styles';

import animationStyles from './Rotations.module.css';

interface RotationsProps extends WithStoreProps {
  shiftIdToShowRotationForm?: Shift['id'] | 'new';
  scheduleId: Schedule['id'];
  onShowRotationForm: (shiftId: Shift['id'] | 'new') => void;
  onClick: (id: Shift['id'] | 'new') => void;
  onShowOverrideForm: (shiftId: 'new', shiftStart: dayjs.Dayjs, shiftEnd: dayjs.Dayjs) => void;
  onShowShiftSwapForm: (id: ShiftSwap['id'] | 'new', params?: Partial<ShiftSwap>) => void;
  onCreate: () => void;
  onUpdate: () => void;
  onDelete: () => void;
  onShiftSwapRequest: (beneficiary: ApiSchemas['User']['pk'], swap_start: string, swap_end: string) => void;
  disabled: boolean;
  filters: ScheduleFiltersType;
  onSlotClick?: (event: Event) => void;
  theme: GrafanaTheme2;
}

interface RotationsState {
  layerPriority?: Layer['priority'];
  shiftStartToShowRotationForm?: dayjs.Dayjs;
  shiftEndToShowRotationForm?: dayjs.Dayjs;
}

@observer
class _Rotations extends Component<RotationsProps, RotationsState> {
  state: RotationsState = {
    layerPriority: undefined,
    shiftStartToShowRotationForm: undefined,
    shiftEndToShowRotationForm: undefined,
  };

  render() {
    const {
      scheduleId,
      onCreate,
      onUpdate,
      onDelete,
      store,
      shiftIdToShowRotationForm,
      disabled,
      filters,
      onShowShiftSwapForm,
      onSlotClick,
      theme,
    } = this.props;
    const { layerPriority, shiftStartToShowRotationForm, shiftEndToShowRotationForm } = this.state;

    const base = 7 * 24 * 60; // in minutes
    const diff = store.timezoneStore.currentDateInSelectedTimezone.diff(
      store.timezoneStore.calendarStartDate,
      'minutes'
    );

    const currentTimeX = diff / base;

    const currentTimeHidden = currentTimeX < 0 || currentTimeX > 1;

    const layers = getLayersFromStore(store, scheduleId, store.timezoneStore.calendarStartDate);

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
    const styles = getRotationsStyles(theme);

    return (
      <>
        <div className={styles.root}>
          <div className={styles.header}>
            <HorizontalGroup justify="space-between">
              <div className={styles.title}>
                <Text.Title level={4} type="primary">
                  Rotations
                </Text.Title>
              </div>
              <HorizontalGroup>
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
                  <Button
                    variant="primary"
                    icon="plus"
                    onClick={() => this.handleAddLayer(nextPriority, store.timezoneStore.calendarStartDate)}
                  >
                    Add rotation
                  </Button>
                )}
              </HorizontalGroup>
            </HorizontalGroup>
          </div>
          <div className={styles.rotationsPlusTitle}>
            {layers && layers.length ? (
              <TransitionGroup>
                {layers.map((layer, layerIndex) => (
                  <CSSTransition
                    key={layerIndex}
                    timeout={DEFAULT_TRANSITION_TIMEOUT}
                    classNames={{ ...animationStyles }}
                  >
                    <div id={`layer${layer.priority}`} className={styles.layer}>
                      <div className={styles.layerTitle}>
                        <HorizontalGroup spacing="sm" justify="center">
                          <Text type="secondary">Layer {layer.priority}</Text>
                        </HorizontalGroup>
                      </div>
                      <div className={styles.headerPlusContent}>
                        <TimelineMarks />
                        {!currentTimeHidden && (
                          <div className={styles.currentTime} style={{ left: `${currentTimeX * 100}%` }} />
                        )}
                        <TransitionGroup className={styles.rotations}>
                          {layer.shifts.map(({ shiftId, isPreview, events }, rotationIndex) => (
                            <CSSTransition
                              key={rotationIndex}
                              timeout={DEFAULT_TRANSITION_TIMEOUT}
                              classNames={{ ...animationStyles }}
                            >
                              <Rotation
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
                <div id={`layer1`} className={styles.layer}>
                  <div className={styles.layerTitle}>
                    <HorizontalGroup spacing="sm" justify="center">
                      <Text type="secondary">Layer 1</Text>
                    </HorizontalGroup>
                  </div>
                  <div className={styles.headerPlusContent}>
                    <div className={styles.currentTime} style={{ left: `${currentTimeX * 100}%` }} />
                    <TimelineMarks />
                    <div className={styles.rotations}>
                      <Rotation
                        onClick={(shiftStart, shiftEnd) => {
                          this.handleAddLayer(nextPriority, shiftStart, shiftEnd);
                        }}
                        events={[]}
                        layerIndex={0}
                        rotationIndex={0}
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}
            {nextPriority > 1 && (
              <div
                className={styles.addRotationsLayer}
                onClick={() => {
                  if (disabled) {
                    return;
                  }
                  this.handleAddLayer(nextPriority, store.timezoneStore.calendarStartDate);
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
    const { disabled, store } = this.props;

    if (disabled) {
      return;
    }

    this.setState(
      {
        layerPriority: option.value,
        shiftStartToShowRotationForm: store.timezoneStore.calendarStartDate,
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

export const Rotations = withMobXProviderContext(withTheme2(_Rotations));
