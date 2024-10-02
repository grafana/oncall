import React, { useCallback, useEffect, useMemo, useState } from 'react';

import { cx } from '@emotion/css';
import {
  Alert,
  Button,
  Field,
  Icon,
  IconButton,
  InlineSwitch,
  Select,
  Switch,
  Tooltip,
  Stack,
  useStyles2,
} from '@grafana/ui';
import dayjs from 'dayjs';
import { GRAFANA_HEADER_HEIGHT, StackSize } from 'helpers/consts';
import { useDebouncedCallback, useIsLoading, useResize } from 'helpers/hooks';
import { observer } from 'mobx-react';
import Draggable, { DraggableData, DraggableEvent } from 'react-draggable';

import { Block } from 'components/GBlock/Block';
import { Modal } from 'components/Modal/Modal';
import { Tag } from 'components/Tag/Tag';
import { Text } from 'components/Text/Text';
import { UserGroups } from 'components/UserGroups/UserGroups';
import { RemoteSelect } from 'containers/RemoteSelect/RemoteSelect';
import {
  dayJSAddWithDSTFixed,
  getRepeatShiftsEveryOptions,
  putDownMaxValues,
  reduceTheLastUnitValue,
  repeatEveryInSeconds,
  repeatEveryPeriodMultiplier,
  repeatEveryPeriodToNextPeriodCount,
  repeatEveryPeriodToUnitName,
  repeatEveryPeriodToUnitNameShortened,
  repeatEveryToTimeUnits,
  secondsToTimeUnits,
  shiftToLower,
  TimeUnit,
  timeUnitsToSeconds,
  TIME_UNITS_ORDER,
  getDraggableModalCoordinatesOnInit,
} from 'containers/RotationForm/RotationForm.helpers';
import { RepeatEveryPeriod } from 'containers/RotationForm/RotationForm.types';
import { DateTimePicker } from 'containers/RotationForm/parts/DateTimePicker';
import { DaysSelector } from 'containers/RotationForm/parts/DaysSelector';
import { DeletionModal } from 'containers/RotationForm/parts/DeletionModal';
import { TimeUnitSelector } from 'containers/RotationForm/parts/TimeUnitSelector';
import { UserItem } from 'containers/RotationForm/parts/UserItem';
import { calculateScheduleFormOffset } from 'containers/Rotations/Rotations.helpers';
import { ActionKey } from 'models/loader/action-keys';
import { getShiftName } from 'models/schedule/schedule.helpers';
import { Schedule, Shift } from 'models/schedule/schedule.types';
import { ApiSchemas } from 'network/oncall-api/api.types';
import {
  getDateTime,
  getSelectedDays,
  getUTCByDay,
  getUTCString,
  getUTCWeekStart,
  getWeekStartString,
  toDateWithTimezoneOffset,
  toDateWithTimezoneOffsetAtMidnight,
} from 'pages/schedule/Schedule.helpers';
import { useStore } from 'state/useStore';

import { getRotationFormStyles } from './RotationForm.styles';

interface RotationFormProps {
  layerPriority: number;
  onHide: () => void;
  scheduleId: Schedule['id'];
  shiftId: Shift['id'] | 'new';
  shiftStart?: dayjs.Dayjs;
  shiftEnd?: dayjs.Dayjs;
  onCreate: () => void;
  onUpdate: () => void;
  onDelete: () => void;
  shiftColor?: string;
  onShowRotationForm: (shiftId: Shift['id']) => void;
}

const getStartShift = (start: dayjs.Dayjs, timezoneOffset: number, isNewRotation = false) => {
  if (isNewRotation) {
    // default to midnight for new rotations
    return toDateWithTimezoneOffsetAtMidnight(start, timezoneOffset);
  }

  // not always midnight
  return toDateWithTimezoneOffset(start, timezoneOffset);
};

export const RotationForm = observer((props: RotationFormProps) => {
  const store = useStore();

  const {
    onHide,
    onCreate,
    scheduleId,
    onUpdate,
    onDelete,
    layerPriority,
    shiftId,
    shiftStart: propsShiftStart = store.timezoneStore.calendarStartDate,
    shiftEnd: propsShiftEnd,
    shiftColor = '#3D71D9',
    onShowRotationForm,
  } = props;

  const shift = store.scheduleStore.shifts[shiftId];
  const styles = useStyles2(getRotationFormStyles);

  const [startRotationFromUserIndex, setStartRotationFromUserIndex] = useState(0);

  const isCreating = useIsLoading(ActionKey.CREATE_ONCALL_SHIFT);
  const isUpdating = useIsLoading(ActionKey.UPDATE_ONCALL_SHIFT);
  const isSubmitting = isCreating || isUpdating;

  const [errors, setErrors] = useState<{ [key: string]: string[] }>({});
  const [bounds, setDraggableBounds] = useState<{ left: number; right: number; top: number; bottom: number }>(
    undefined
  );

  const [rotationName, setRotationName] = useState(`[L${layerPriority}] Rotation`);
  const [isOpen, setIsOpen] = useState(false);
  const [offsetTop, setOffsetTop] = useState(GRAFANA_HEADER_HEIGHT + 10);
  const [draggablePosition, setDraggablePosition] = useState<{ x: number; y: number }>(undefined);

  const [shiftStart, setShiftStart] = useState<dayjs.Dayjs>(
    getStartShift(propsShiftStart, store.timezoneStore.selectedTimezoneOffset, shiftId === 'new')
  );

  const [shiftEnd, setShiftEnd] = useState<dayjs.Dayjs>(
    propsShiftEnd?.utcOffset(store.timezoneStore.selectedTimezoneOffset) || shiftStart.add(1, 'day')
  );

  const [activePeriod, setActivePeriod] = useState<number>(undefined);
  const [shiftPeriodDefaultValue, setShiftPeriodDefaultValue] = useState<number>(undefined);

  const [rotationStart, setRotationStart] = useState<dayjs.Dayjs>(shiftStart);
  const [endLess, setEndless] = useState<boolean>(shift?.until === undefined ? true : !Boolean(shift.until));
  const [rotationEnd, setRotationEnd] = useState<dayjs.Dayjs>(shiftStart.add(1, 'month'));

  const [recurrenceNum, setRecurrenceNum] = useState(1);
  const [recurrencePeriod, setRecurrencePeriod] = useState(RepeatEveryPeriod.DAYS);

  const [isMaskedByWeekdays, setIsMaskedByWeekdays] = useState(false);
  const [isLimitShiftEnabled, setIsLimitShiftEnabled] = useState(false);

  const [selectedDays, setSelectedDays] = useState<string[]>([]);

  const [userGroups, setUserGroups] = useState([]);

  const [showDeleteRotationConfirmation, setShowDeleteRotationConfirmation] = useState(false);
  const debouncedOnResize = useDebouncedCallback(onResize, 250);

  useResize(debouncedOnResize);

  useEffect(() => {
    if (rotationStart.isBefore(shiftStart)) {
      setRotationStart(shiftStart);
    }
  }, [rotationStart, shiftStart]);

  useEffect(() => {
    if (!isMaskedByWeekdays) {
      setSelectedDays([]);
    }
  }, [isMaskedByWeekdays]);

  useEffect(() => {
    (async () => {
      if (isOpen) {
        setOffsetTop(await calculateScheduleFormOffset(`.${cx('draggable')}`));
      }
    })();
  }, [isOpen]);

  const handleChangeEndless = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      setEndless(!event.currentTarget.checked);
    },
    [endLess]
  );

  const handleDeleteClick = useCallback(async (force: boolean) => {
    await store.scheduleStore.deleteOncallShift(shiftId, force);
    onDelete();
  }, []);

  useEffect(() => {
    if (shiftId !== 'new') {
      store.scheduleStore.updateOncallShift(shiftId);
    }
  }, [shiftId]);

  useEffect(() => {
    if (shiftId === 'new') {
      updatePreview();
    }
  }, []);

  const updatePreview = async () => {
    setErrors({});

    try {
      await store.scheduleStore.updateRotationPreview(
        scheduleId,
        shiftId,
        store.timezoneStore.calendarStartDate,
        false,
        params
      );
    } catch (err) {
      onError(err);
    } finally {
      // wait until a scroll to the "Rotations" happened
      setTimeout(() => {
        setIsOpen(true);
      }, 100);
    }
  };

  const onError = (error) => {
    if (error.response?.data) {
      setErrors(error.response.data);
    }
  };

  const handleChange = useDebouncedCallback(updatePreview, 200);

  const params = useMemo(
    () => ({
      rotation_start: getUTCString(rotationStart),
      until: endLess ? null : getUTCString(rotationEnd),
      shift_start: getUTCString(shiftStart),
      shift_end: getUTCString(shiftEnd),
      rolling_users: userGroups,
      interval: recurrenceNum,
      frequency: recurrencePeriod,
      by_day: getUTCByDay({
        dayOptions: store.scheduleStore.byDayOptions,
        by_day: selectedDays,
        moment: store.timezoneStore.getDateInSelectedTimezone(shiftStart),
      }),
      week_start: getUTCWeekStart(
        store.scheduleStore.byDayOptions,
        store.timezoneStore.getDateInSelectedTimezone(shiftStart)
      ),
      priority_level: shiftId === 'new' ? layerPriority : shift?.priority_level,
      name: rotationName,
      start_rotation_from_user_index: startRotationFromUserIndex,
    }),
    [
      rotationStart,
      rotationEnd,
      shiftStart,
      shiftEnd,
      userGroups,
      recurrenceNum,
      recurrencePeriod,
      selectedDays,
      shiftId,
      layerPriority,
      shift,
      endLess,
      rotationName,
      startRotationFromUserIndex,
      store.timezoneStore.selectedTimezoneOffset,
    ]
  );

  useEffect(handleChange, [params, store.timezoneStore.calendarStartDate, store.timezoneStore.selectedTimezoneOffset]);

  const create = useCallback(async () => {
    try {
      await store.scheduleStore.createRotation(scheduleId, false, { ...params, name: rotationName });
      onCreate();
    } catch (err) {
      onError(err);
    }
  }, [scheduleId, shiftId, params]);

  const update = useCallback(async () => {
    try {
      await store.scheduleStore.updateRotation(shiftId, params);
      onUpdate();
    } catch (err) {
      onError(err);
    }
  }, [shiftId, params]);

  const updateAsNew = useCallback(async () => {
    try {
      await store.scheduleStore.updateRotationAsNew(shiftId, params);
      onUpdate();
    } catch (err) {
      onError(err);
    }
  }, [shiftId, params]);

  const handleEditNewerRotationClick = useCallback(() => {
    onShowRotationForm(shift.updated_shift);
  }, [shift?.updated_shift]);

  const onRecurrencePeriodChange = useCallback(
    (value) => {
      setShiftPeriodDefaultValue(undefined);
      setRecurrencePeriod(value);

      if (value === RepeatEveryPeriod.MONTHS && !isMaskedByWeekdays) {
        setIsLimitShiftEnabled(false);
      }

      if (!isLimitShiftEnabled) {
        if (isMaskedByWeekdays) {
          setShiftEnd(
            dayJSAddWithDSTFixed({
              baseDate: shiftStart,
              addParams: [24, 'hours'],
            })
          );
        } else {
          setShiftEnd(
            dayJSAddWithDSTFixed({
              baseDate: shiftStart,
              addParams: [recurrenceNum, repeatEveryPeriodToUnitName[value]],
            })
          );
        }
      }
    },
    [isLimitShiftEnabled, isMaskedByWeekdays, recurrenceNum, shiftStart]
  );

  const handleRepeatEveryValueChange = (option) => {
    const value = Math.floor(Number(option.value));
    if (isNaN(value) || value < 1) {
      return;
    }

    setShiftPeriodDefaultValue(undefined);
    setRecurrenceNum(value);

    if (!isLimitShiftEnabled && !isMaskedByWeekdays) {
      setShiftEnd(
        dayJSAddWithDSTFixed({
          baseDate: rotationStart,
          addParams: [value, repeatEveryPeriodToUnitName[recurrencePeriod]],
        })
      );
    }
  };

  const handleRotationStartChange = (value: dayjs.Dayjs) => {
    setRotationStart(value);
    setShiftStart(value);

    let addParams;
    if (isLimitShiftEnabled) {
      addParams = [activePeriod, 'seconds'];
    } else if (isMaskedByWeekdays) {
      addParams = [24, 'hours'];
    } else {
      addParams = [recurrenceNum, repeatEveryPeriodToUnitName[recurrencePeriod]];
    }
    setShiftEnd(dayJSAddWithDSTFixed({ baseDate: value, addParams }));
  };

  const handleActivePeriodChange = useCallback(
    (value) => {
      setActivePeriod(value);
      setShiftEnd(
        dayJSAddWithDSTFixed({
          baseDate: shiftStart,
          addParams: [value, 'seconds'],
        })
      );
    },
    [shiftStart]
  );

  const handleRotationNameChange = useCallback(
    (name: string) => {
      setRotationName(name);
    },
    [shiftId, params, shift]
  );

  const onMaskedByWeekdaysSwitch = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const value = event.currentTarget.checked;
      const disableLimitShift = !value && recurrencePeriod === RepeatEveryPeriod.MONTHS;

      setIsMaskedByWeekdays(value);

      if (disableLimitShift) {
        setIsLimitShiftEnabled(false);
      }

      if (value && shiftEnd.diff(shiftStart, 'hours') > 24) {
        setShiftEnd(
          dayJSAddWithDSTFixed({
            baseDate: shiftStart,
            addParams: [24, 'hours'],
          })
        );
      } else {
        if (!isLimitShiftEnabled || disableLimitShift) {
          setShiftEnd(
            dayJSAddWithDSTFixed({
              baseDate: shiftStart,
              addParams: [recurrenceNum, repeatEveryPeriodToUnitName[recurrencePeriod]],
            })
          );
        }
      }
    },
    [isLimitShiftEnabled, shiftStart, shiftEnd, recurrenceNum, recurrencePeriod]
  );

  const onLimitShiftSwitch = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const value = event.currentTarget.checked;
      setIsLimitShiftEnabled(value);

      if (!value) {
        if (isMaskedByWeekdays) {
          setShiftEnd(
            dayJSAddWithDSTFixed({
              baseDate: shiftStart,
              addParams: [24, 'hours'],
            })
          );
        } else {
          setShiftEnd(
            dayJSAddWithDSTFixed({
              baseDate: shiftStart,
              addParams: [recurrenceNum, repeatEveryPeriodToUnitName[recurrencePeriod]],
            })
          );
        }
      }
    },
    [shiftStart, shiftEnd, recurrencePeriod, recurrenceNum, isMaskedByWeekdays]
  );

  useEffect(() => {
    if (shift) {
      setRotationName(getShiftName(shift));

      // use shiftStart as rotationStart for existing shifts
      // (original rotationStart defaulted to the shift creation timestamp)
      const shiftStart = toDateWithTimezoneOffset(dayjs(shift.shift_start), store.timezoneStore.selectedTimezoneOffset);

      setRotationStart(shiftStart);
      setRotationEnd(
        toDateWithTimezoneOffset(
          // always keep the date offseted
          shift.until ? getDateTime(shift.until) : getDateTime(shift.shift_start).add(1, 'month'),
          store.timezoneStore.selectedTimezoneOffset
        )
      );
      setShiftStart(shiftStart);

      const shiftEnd = toDateWithTimezoneOffset(dayjs(shift.shift_end), store.timezoneStore.selectedTimezoneOffset);
      setShiftEnd(shiftEnd);

      setRecurrenceNum(shift.interval);
      setRecurrencePeriod(shift.frequency);
      setSelectedDays(
        getSelectedDays({
          dayOptions: store.scheduleStore.byDayOptions,
          by_day: shift.by_day,
          moment: store.timezoneStore.getDateInSelectedTimezone(shiftStart),
        })
      );

      setIsMaskedByWeekdays(Boolean(shift.by_day?.length));

      const isMonthlyRecurrence = shift.frequency === RepeatEveryPeriod.MONTHS;
      const activeOnSelectedPartOfDay =
        ((!isMaskedByWeekdays &&
          repeatEveryInSeconds(shift.frequency, shift.interval) !== shiftEnd.diff(shiftStart, 'seconds')) ||
          (isMaskedByWeekdays && shiftEnd.diff(shiftStart, 'hour') < 24)) &&
        // Disallow for Monthly view, except if it's masked by week days
        (!isMonthlyRecurrence || (isMonthlyRecurrence && isMaskedByWeekdays));

      setIsLimitShiftEnabled(activeOnSelectedPartOfDay);
      if (activeOnSelectedPartOfDay) {
        const activePeriod = shiftEnd.diff(shiftStart, 'seconds');

        setActivePeriod(activePeriod);
        setShiftPeriodDefaultValue(activePeriod);
      }

      setUserGroups(shift.rolling_users);
      setStartRotationFromUserIndex(shift.start_rotation_from_user_index);
    }
  }, [shift]);

  useEffect(() => {
    if (shift) {
      // for existing rotations
      handleRotationStartChange(toDateWithTimezoneOffset(rotationStart, store.timezoneStore.selectedTimezoneOffset));
      setRotationEnd(toDateWithTimezoneOffset(rotationEnd, store.timezoneStore.selectedTimezoneOffset));

      setSelectedDays(
        getSelectedDays({
          dayOptions: store.scheduleStore.byDayOptions,
          by_day: shift.by_day,
          moment: store.timezoneStore.getDateInSelectedTimezone(shiftStart),
        })
      );
    } else {
      // for new rotations
      handleRotationStartChange(toDateWithTimezoneOffset(rotationStart, store.timezoneStore.selectedTimezoneOffset));

      setShiftEnd(toDateWithTimezoneOffset(shiftEnd, store.timezoneStore.selectedTimezoneOffset));

      // not behind an "if" such that it will reflect correct value after toggle gets switched
      setRotationEnd(toDateWithTimezoneOffset(rotationEnd, store.timezoneStore.selectedTimezoneOffset));
    }
  }, [store.timezoneStore.selectedTimezoneOffset]);

  const isFormValid = useMemo(() => !Object.keys(errors).length, [errors]);

  const hasUpdatedShift = shift && shift.updated_shift;
  const ended = shift && shift.until && getDateTime(shift.until).isBefore(dayjs());

  const disabled = hasUpdatedShift || ended || isSubmitting;

  return (
    <>
      <Modal
        top="0"
        isOpen={isOpen}
        width="430px"
        onDismiss={onHide}
        contentElement={(props, children) => (
          <Draggable
            handle=".drag-handler"
            defaultClassName={'draggable'}
            positionOffset={{ x: 0, y: offsetTop }}
            position={draggablePosition}
            bounds={{ ...bounds } || 'body'}
            onStart={onDraggableInit}
            onStop={(_e, data) => setDraggablePosition({ x: data.x, y: data.y })}
          >
            <div {...props}>{children}</div>
          </Draggable>
        )}
      >
        <div data-testid="rotation-form">
          <div>
            <Stack justifyContent="space-between">
              <Stack gap={StackSize.sm}>
                {shiftId === 'new' && <Tag color={shiftColor}>New</Tag>}
                <Text.Title editModalTitle="Rotation name" onTextChange={handleRotationNameChange} level={5} editable>
                  {rotationName}
                </Text.Title>
              </Stack>
              <Stack>
                {shiftId !== 'new' && (
                  <IconButton
                    variant="secondary"
                    tooltip="Delete"
                    name="trash-alt"
                    onClick={() => setShowDeleteRotationConfirmation(true)}
                  />
                )}
                <IconButton aria-label="Drag" variant="secondary" className="drag-handler" name="draggabledots" />
                <IconButton
                  name="times"
                  variant="secondary"
                  tooltip={shiftId === 'new' ? 'Cancel' : 'Close'}
                  onClick={onHide}
                />
              </Stack>
            </Stack>
          </div>
          <div className={styles.container}>
            <div>
              <Stack direction="column" gap={StackSize.none}>
                {hasUpdatedShift && (
                  <Block bordered className={styles.updatedShiftInfo}>
                    <Stack direction="column">
                      <Stack alignItems="flex-start">
                        <Icon name="info-circle" size="md"></Icon>
                        <Text>
                          This rotation is read-only because it has newer version.{' '}
                          <Text onClick={handleEditNewerRotationClick} type="link" clickable>
                            Edit the newer version
                          </Text>{' '}
                          instead
                        </Text>
                      </Stack>
                    </Stack>
                  </Block>
                )}
                {!hasUpdatedShift && ended && (
                  <div className={styles.updatedShiftInfo}>
                    <Stack direction="column">
                      <Alert severity="info" title={(<Text>This rotation is over</Text>) as unknown as string} />
                    </Stack>
                  </div>
                )}
                <div className={styles.twoFields}>
                  <Field
                    label={
                      <Text type="primary" size="small">
                        Starts
                      </Text>
                    }
                    data-testid="rotation-start"
                  >
                    <DateTimePicker
                      value={rotationStart}
                      utcOffset={store.timezoneStore.selectedTimezoneOffset}
                      onChange={handleRotationStartChange}
                      error={errors.rotation_start}
                      disabled={disabled}
                    />
                  </Field>
                  <Field
                    label={
                      <Stack gap={StackSize.xs}>
                        <Text type="primary" size="small">
                          Ends
                        </Text>
                        <InlineSwitch
                          className={styles.inlineSwitch}
                          transparent
                          value={!endLess}
                          onChange={handleChangeEndless}
                          disabled={disabled}
                        />
                      </Stack>
                    }
                    data-testid="rotation-end"
                  >
                    {endLess ? (
                      <div style={{ lineHeight: '32px' }}>
                        <Text type="secondary">Endless</Text>
                      </div>
                    ) : (
                      <DateTimePicker
                        value={rotationEnd}
                        utcOffset={store.timezoneStore.selectedTimezoneOffset}
                        onChange={setRotationEnd}
                        error={errors.until}
                        disabled={disabled}
                      />
                    )}
                  </Field>
                </div>
                <div className={styles.twoFields}>
                  <Field
                    invalid={Boolean(errors.interval)}
                    error={'Invalid recurrence period'}
                    label={
                      <Stack gap={StackSize.sm}>
                        <Text type="primary" size="small">
                          Recurrence period
                        </Text>
                        <Tooltip content="Time interval when users shifts are rotated. Shifts active period can be customised by days of the week and hours during a day.">
                          <Icon name="info-circle" size="md"></Icon>
                        </Tooltip>
                      </Stack>
                    }
                  >
                    <Select
                      maxMenuHeight={120}
                      value={recurrenceNum}
                      options={getRepeatShiftsEveryOptions(recurrencePeriod)}
                      onChange={handleRepeatEveryValueChange}
                      disabled={disabled}
                      allowCustomValue
                    />
                  </Field>
                  <Field label="">
                    <RemoteSelect
                      showSearch={false}
                      href="/oncall_shifts/frequency_options/"
                      value={recurrencePeriod}
                      onChange={onRecurrencePeriodChange}
                      disabled={disabled}
                    />
                  </Field>
                </div>
                <Stack direction="column" gap={StackSize.md}>
                  <Stack direction="column">
                    <Stack alignItems="flex-start">
                      <Switch disabled={disabled} value={isMaskedByWeekdays} onChange={onMaskedByWeekdaysSwitch} />
                      <Stack direction="column">
                        <Text type="secondary">Mask by weekdays</Text>
                        {isMaskedByWeekdays && (
                          <DaysSelector
                            options={store.scheduleStore.byDayOptions}
                            value={selectedDays}
                            onChange={setSelectedDays}
                            weekStart={getWeekStartString()}
                            disabled={disabled}
                          />
                        )}
                      </Stack>
                    </Stack>

                    <Stack alignItems="flex-start">
                      <Switch
                        disabled={isSelectedPartOfDayDisabled()}
                        value={isLimitShiftEnabled}
                        onChange={onLimitShiftSwitch}
                      />
                      <Stack direction="column">
                        <Text type="secondary">Limit each shift length</Text>
                        {isLimitShiftEnabled && (
                          <ShiftPeriod
                            repeatEveryPeriod={isMaskedByWeekdays ? RepeatEveryPeriod.HOURS : recurrencePeriod}
                            repeatEveryValue={
                              isMaskedByWeekdays
                                ? recurrencePeriod === RepeatEveryPeriod.HOURS
                                  ? Math.min(recurrenceNum, 24)
                                  : 24
                                : recurrenceNum
                            }
                            defaultValue={shiftPeriodDefaultValue}
                            shiftStart={shiftStart}
                            onChange={handleActivePeriodChange}
                            disabled={disabled}
                            errors={errors}
                          />
                        )}
                        {isMaskedByWeekdays && (
                          <Text type="secondary">
                            Since masking by weekdays is enabled, each shift length may not exceed 24hs, and each shift
                            will repeat every day
                          </Text>
                        )}
                      </Stack>
                    </Stack>
                  </Stack>
                </Stack>
                <div style={{ marginTop: '16px' }}>
                  <Stack>
                    <Text size="small">Users</Text>
                    <Tooltip content="By default each new user creates new rotation group. You can customise groups by dragging.">
                      <Icon name="info-circle" size="md" />
                    </Tooltip>
                  </Stack>
                </div>
                <UserGroups
                  disabled={disabled}
                  value={userGroups}
                  onChange={setUserGroups}
                  isMultipleGroups={true}
                  renderUser={(pk: ApiSchemas['User']['pk']) => (
                    <UserItem
                      pk={pk}
                      shiftColor={shiftColor}
                      shiftStart={params.shift_start}
                      shiftEnd={params.shift_end}
                    />
                  )}
                  showError={Boolean(errors.rolling_users)}
                />
              </Stack>
            </div>
          </div>
          <div>
            <Stack justifyContent="space-between">
              <Text type="secondary">
                Current timezone: <Text type="primary">{store.timezoneStore.selectedTimezoneLabel}</Text>
              </Text>
              <Stack>
                {shiftId !== 'new' && (
                  <Tooltip content="Stop the current rotation and start a new one">
                    <Button disabled={disabled} variant="secondary" onClick={updateAsNew}>
                      Save as new
                    </Button>
                  </Tooltip>
                )}
                {shiftId === 'new' ? (
                  <Button variant="primary" onClick={create} disabled={disabled || !isFormValid}>
                    Create
                  </Button>
                ) : (
                  <Tooltip content="Update the current rotation, even events in the past">
                    <Button variant="primary" onClick={update} disabled={disabled || !isFormValid}>
                      Update
                    </Button>
                  </Tooltip>
                )}
              </Stack>
            </Stack>
          </div>
        </div>
      </Modal>
      {showDeleteRotationConfirmation && (
        <DeletionModal onHide={() => setShowDeleteRotationConfirmation(false)} onConfirm={handleDeleteClick} />
      )}
    </>
  );

  function isSelectedPartOfDayDisabled() {
    // Disable Shift length limit if Monday is enabled without masked weekdays
    if (recurrencePeriod === RepeatEveryPeriod.MONTHS && !isMaskedByWeekdays) {
      return true;
    }

    return disabled;
  }

  async function onResize() {
    setOffsetTop(await calculateScheduleFormOffset(`.${cx('draggable')}`));

    setDraggablePosition({ x: 0, y: 0 });
  }

  function onDraggableInit(_e: DraggableEvent, data: DraggableData) {
    if (!data) {
      return;
    }

    const bounds = getDraggableModalCoordinatesOnInit(data, offsetTop);
    setDraggableBounds(bounds);
  }
});

interface ShiftPeriodProps {
  repeatEveryPeriod: number;
  repeatEveryValue: number;
  defaultValue: number;
  shiftStart: dayjs.Dayjs;
  onChange: (value: number) => void;
  disabled: boolean;
  errors: any;
}

const ShiftPeriod = ({
  repeatEveryPeriod,
  repeatEveryValue,
  defaultValue,
  onChange,
  errors,
  disabled,
}: ShiftPeriodProps) => {
  const [timeUnits, setTimeUnits] = useState<TimeUnit[]>([]);
  const styles = useStyles2(getRotationFormStyles);

  useEffect(() => {
    if (defaultValue === undefined) {
      setTimeUnits(reduceTheLastUnitValue(shiftToLower(repeatEveryToTimeUnits(repeatEveryPeriod, repeatEveryValue))));
    } else {
      setTimeUnits(
        putDownMaxValues(secondsToTimeUnits(defaultValue, repeatEveryPeriod), repeatEveryPeriod, repeatEveryValue)
      );
    }
  }, [repeatEveryPeriod, repeatEveryValue]);

  useEffect(() => {
    onChange(timeUnitsToSeconds(timeUnits));
  }, [timeUnits]);

  const getTimeUnitChangeHandler = (unit: RepeatEveryPeriod) => {
    return (value) => {
      const newTimeUnits = [...timeUnits];

      const timeUnit = newTimeUnits.find((timeUnit) => timeUnit.unit === unit);
      timeUnit.value = value;

      setTimeUnits(newTimeUnits);
    };
  };

  const duration = useMemo(
    () =>
      timeUnits
        .map((timeUnit) => {
          return timeUnit.value + repeatEveryPeriodToUnitNameShortened[timeUnit.unit];
        })
        .join(''),
    [timeUnits]
  );

  const getTimeUnitDeleteHandler = (unit: RepeatEveryPeriod) => {
    return () => {
      const newTimeUnits = [...timeUnits];

      const timeUnitIndex = newTimeUnits.findIndex((timeUnit) => timeUnit.unit === unit);
      newTimeUnits.splice(timeUnitIndex, 1);

      setTimeUnits(newTimeUnits);
    };
  };

  const unitToCreate = useMemo(() => {
    if (!timeUnits.length) {
      return reduceTheLastUnitValue(shiftToLower(repeatEveryToTimeUnits(repeatEveryPeriod, repeatEveryValue)))[0];
    }

    const minIndex = TIME_UNITS_ORDER.findIndex((tu) => tu === repeatEveryPeriod);

    const lastTimeUnit = timeUnits[timeUnits.length - 1];
    const currentIndex = lastTimeUnit ? TIME_UNITS_ORDER.findIndex((tu) => tu === lastTimeUnit.unit) : -1;

    const unit = TIME_UNITS_ORDER[Math.max(minIndex, currentIndex + 1)];

    if (unit === undefined) {
      return undefined;
    }

    const maxValue = Math.min(
      Math.floor(
        (repeatEveryInSeconds(repeatEveryPeriod, repeatEveryValue) - timeUnitsToSeconds(timeUnits)) /
          repeatEveryPeriodMultiplier[unit]
      ),
      repeatEveryPeriodToNextPeriodCount[unit]
    );

    if (maxValue === 0) {
      return undefined;
    }

    return { unit, value: 1, maxValue: maxValue - 1 };
  }, [timeUnits]);

  const handleTimeUnitAdd = useCallback(() => {
    const newTimeUnits = [...timeUnits, unitToCreate];

    setTimeUnits(newTimeUnits);
  }, [unitToCreate]);

  return (
    <Stack direction="column">
      {timeUnits.map((unit, index: number, arr) => (
        <Stack key={unit.unit}>
          <TimeUnitSelector
            disabled={disabled}
            unit={unit.unit}
            value={unit.value}
            onChange={getTimeUnitChangeHandler(unit.unit)}
            maxValue={unit.maxValue}
            className={styles.timeUnit}
          />
          {index === arr.length - 1 && (
            <Button
              disabled={disabled}
              tooltip="Remove segment"
              variant="secondary"
              icon="times"
              size="sm"
              onClick={getTimeUnitDeleteHandler(unit.unit)}
            />
          )}
          {index === arr.length - 1 && unitToCreate !== undefined && (
            <Button
              disabled={disabled}
              tooltip="Add segment"
              variant="secondary"
              icon="plus"
              size="sm"
              onClick={handleTimeUnitAdd}
            />
          )}
        </Stack>
      ))}
      {timeUnits.length === 0 && unitToCreate !== undefined && (
        <Button disabled={disabled} variant="secondary" icon="plus" size="sm" onClick={handleTimeUnitAdd}>
          Add time segment
        </Button>
      )}
      <Text type="secondary">({duration || '0m'})</Text>
      {errors.shift_end && <Text type="danger">Shift length must be greater than zero</Text>}
    </Stack>
  );
};
