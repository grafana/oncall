import React, { Component } from 'react';

import { css, cx } from '@emotion/css';
import { GrafanaTheme2, SelectableValue } from '@grafana/data';
import { ValuePicker, Button, Tooltip, withTheme2, Stack } from '@grafana/ui';
import dayjs from 'dayjs';
import { HTML_ID } from 'helpers/DOM';
import { UserActions } from 'helpers/authorization/authorization';
import { observer } from 'mobx-react';
import { CSSTransition, TransitionGroup } from 'react-transition-group';

import { ScheduleFiltersType } from 'components/ScheduleFilters/ScheduleFilters.types';
import { Tag } from 'components/Tag/Tag';
import { Text } from 'components/Text/Text';
import { Rotation } from 'containers/Rotation/Rotation';
import { RotationForm } from 'containers/RotationForm/RotationForm';
import { TimelineMarks } from 'containers/TimelineMarks/TimelineMarks';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { getColor, getLayersFromStore, scheduleViewToDaysInOneRow } from 'models/schedule/schedule.helpers';
import { Schedule, ScheduleType, Shift, ShiftSwap, Event, Layer } from 'models/schedule/schedule.types';
import { getCurrentTimeX, toDateWithTimezoneOffset } from 'pages/schedule/Schedule.helpers';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';

import { getAnimationClasses } from './Animations.styles';
import { DEFAULT_TRANSITION_TIMEOUT } from './Rotations.config';
import { findColor, getCalendarStartDateInTimezone } from './Rotations.helpers';
import { getRotationsStyles } from './Rotations.styles';

interface RotationsProps extends WithStoreProps {
  shiftIdToShowRotationForm?: Shift['id'] | 'new';
  layerPriorityToShowRotationForm?: Layer['priority'];
  scheduleId: Schedule['id'];
  onShowRotationForm: (shiftId: Shift['id'] | 'new', layerPriority?: Layer['priority']) => void;
  onShowOverrideForm: (shiftId: 'new', shiftStart: dayjs.Dayjs, shiftEnd: dayjs.Dayjs) => void;
  onShowShiftSwapForm: (id: ShiftSwap['id'] | 'new', params?: Partial<ShiftSwap>) => void;
  onCreate: () => void;
  onUpdate: () => void;
  onDelete: () => void;
  disabled: boolean;
  filters: ScheduleFiltersType;
  onSlotClick?: (event: Event) => void;
  theme: GrafanaTheme2;
}

interface RotationsState {
  shiftStartToShowRotationForm?: dayjs.Dayjs;
  shiftEndToShowRotationForm?: dayjs.Dayjs;
}

@observer
class _Rotations extends Component<RotationsProps, RotationsState> {
  state: RotationsState = {
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
      layerPriorityToShowRotationForm,
      theme,
    } = this.props;

    const { shiftStartToShowRotationForm, shiftEndToShowRotationForm } = this.state;

    const { selectedTimezoneOffset } = store.timezoneStore;

    const currentTimeX = getCurrentTimeX(
      store.timezoneStore.currentDateInSelectedTimezone,
      store.timezoneStore.calendarStartDate,
      scheduleViewToDaysInOneRow[store.scheduleStore.scheduleView] * 24 * 60
    );

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
        <div id={HTML_ID.SCHEDULE_ROTATIONS} className={styles.root}>
          <div className={styles.header}>
            <Stack justifyContent="space-between">
              <Text.Title level={5} type="primary">
                Rotations
              </Text.Title>
              <Stack>
                {disabled ? (
                  isTypeReadOnly ? (
                    <Tooltip content="Ical and API/Terraform rotations are read-only here" placement="top">
                      <div>
                        <Button variant="secondary" icon="plus" disabled>
                          Add rotation
                        </Button>
                      </div>
                    </Tooltip>
                  ) : (
                    <WithPermissionControlTooltip userAction={UserActions.SchedulesWrite}>
                      <Button variant="secondary" icon="plus" disabled>
                        Add rotation
                      </Button>
                    </WithPermissionControlTooltip>
                  )
                ) : options.length > 0 ? (
                  <ValuePicker
                    label="Add rotation"
                    options={options}
                    onChange={this.handleAddRotation}
                    variant="secondary"
                    size="md"
                  />
                ) : (
                  <Button
                    variant="secondary"
                    icon="plus"
                    onClick={() =>
                      this.handleAddLayer(
                        nextPriority,
                        getCalendarStartDateInTimezone(
                          store.timezoneStore.calendarStartDate,
                          store.timezoneStore.selectedTimezoneOffset
                        ),
                        undefined
                      )
                    }
                  >
                    Add rotation
                  </Button>
                )}
              </Stack>
            </Stack>
          </div>
          <div className={styles.rotationsPlusTitle}>
            {layers && layers.length ? (
              <TransitionGroup
                className={css`
                  position: relative;
                `}
              >
                <TimelineMarks />
                {!currentTimeHidden && (
                  <div
                    className={styles.currentTime}
                    style={{
                      left: `${currentTimeX * 100}%`,
                    }}
                  />
                )}
                {layers.map((layer, layerIndex) => (
                  <CSSTransition
                    key={layerIndex}
                    timeout={DEFAULT_TRANSITION_TIMEOUT}
                    classNames={{ ...getAnimationClasses() }}
                  >
                    <div
                      id={`layer${layer.priority}`}
                      className={cx(styles.layer, { [styles.layerFirst]: layerIndex === 0 })}
                    >
                      <Tag className={styles.layerTitle}>
                        <Text size="small" type="primary">
                          Layer {layer.priority}
                        </Text>
                      </Tag>
                      <div
                        className={css`
                          position: relative;
                        `}
                      >
                        <TransitionGroup
                          className={css`
                            position: relative;
                          `}
                        >
                          {layer.shifts.map(({ shiftId, isPreview, events }, rotationIndex) => (
                            <CSSTransition
                              key={rotationIndex}
                              timeout={DEFAULT_TRANSITION_TIMEOUT}
                              classNames={{ ...getAnimationClasses() }}
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
              <div
                className={css`
                  position: relative;
                `}
              >
                <TimelineMarks />
                <div className={styles.currentTime} style={{ left: `${currentTimeX * 100}%` }} />
                <div id="layer1" className={cx(styles.layer, styles.layerFirst)}>
                  <Tag className={styles.layerTitle}>
                    <Text size="small" type="primary">
                      Layer 1
                    </Text>
                  </Tag>
                  <div
                    className={css`
                      position: relative;
                    `}
                  >
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
                <Text type={disabled ? 'disabled' : 'link'}>+ Add new layer with rotation</Text>
              </div>
            )}
          </div>
        </div>
        {shiftIdToShowRotationForm && (
          <RotationForm
            shiftId={shiftIdToShowRotationForm}
            shiftColor={findColor(shiftIdToShowRotationForm, layers)}
            scheduleId={scheduleId}
            layerPriority={layerPriorityToShowRotationForm}
            shiftStart={toDateWithTimezoneOffset(shiftStartToShowRotationForm, selectedTimezoneOffset)}
            shiftEnd={toDateWithTimezoneOffset(shiftEndToShowRotationForm, selectedTimezoneOffset)}
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
      {
        shiftStartToShowRotationForm: shiftStart,
        shiftEndToShowRotationForm: shiftEnd,
      },
      () => {
        this.onShowRotationForm('new', layerPriority);
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
        shiftStartToShowRotationForm: store.timezoneStore.calendarStartDate,
      },
      () => {
        this.onShowRotationForm('new', option.value);
      }
    );
  };

  hideRotationForm = () => {
    this.setState(
      {
        shiftStartToShowRotationForm: undefined,
        shiftEndToShowRotationForm: undefined,
      },
      () => {
        this.onShowRotationForm(undefined, undefined);
      }
    );
  };

  onShowRotationForm = (shiftId: Shift['id'], layerPriority?: Layer['priority']) => {
    const { onShowRotationForm } = this.props;

    onShowRotationForm(shiftId, layerPriority);
  };

  handleShowOverrideForm = (shiftStart: dayjs.Dayjs, shiftEnd: dayjs.Dayjs) => {
    const { onShowOverrideForm } = this.props;

    onShowOverrideForm('new', shiftStart, shiftEnd);
  };
}

export const Rotations = withMobXProviderContext(withTheme2(_Rotations)) as unknown as React.ComponentClass<
  Omit<RotationsProps, 'store' | 'theme'>
>;
