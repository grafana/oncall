import React, { useCallback, useEffect, useMemo, useState } from 'react';

import {
  Button,
  Field,
  HorizontalGroup,
  Icon,
  IconButton,
  InlineSwitch,
  Select,
  Switch,
  Tooltip,
  VerticalGroup,
} from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';
import Draggable from 'react-draggable';

import Block from 'components/GBlock/Block';
import Modal from 'components/Modal/Modal';
import Tag from 'components/Tag/Tag';
import Text from 'components/Text/Text';
import UserGroups from 'components/UserGroups/UserGroups';
import RemoteSelect from 'containers/RemoteSelect/RemoteSelect';
import {
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
} from 'containers/RotationForm/RotationForm.helpers';
import { RepeatEveryPeriod } from 'containers/RotationForm/RotationForm.types';
import DateTimePicker from 'containers/RotationForm/parts/DateTimePicker';
import DaysSelector from 'containers/RotationForm/parts/DaysSelector';
import DeletionModal from 'containers/RotationForm/parts/DeletionModal';
import TimeUnitSelector from 'containers/RotationForm/parts/TimeUnitSelector';
import UserItem from 'containers/RotationForm/parts/UserItem';
import { getShiftName } from 'models/schedule/schedule.helpers';
import { Schedule, Shift } from 'models/schedule/schedule.types';
import { getTzOffsetString } from 'models/timezone/timezone.helpers';
import { Timezone } from 'models/timezone/timezone.types';
import { User } from 'models/user/user.types';
import {
  getDateTime,
  getSelectedDays,
  getStartOfWeek,
  getUTCByDay,
  getUTCString,
  getUTCWeekStart,
  getWeekStartString,
} from 'pages/schedule/Schedule.helpers';
import { useStore } from 'state/useStore';
import { getCoords, waitForElement } from 'utils/DOM';
import { GRAFANA_HEADER_HEIGHT } from 'utils/consts';
import { useDebouncedCallback } from 'utils/hooks';

import styles from './RotationForm.module.css';

const cx = cn.bind(styles);

interface RotationFormProps {
  layerPriority: number;
  onHide: () => void;
  startMoment: dayjs.Dayjs;
  currentTimezone: Timezone;
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

const RotationForm = observer((props: RotationFormProps) => {
  const {
    onHide,
    onCreate,
    startMoment,
    currentTimezone,
    scheduleId,
    onUpdate,
    onDelete,
    layerPriority,
    shiftId,
    shiftStart: propsShiftStart = getStartOfWeek(currentTimezone),
    shiftEnd: propsShiftEnd,
    shiftColor = '#3D71D9',
    onShowRotationForm,
  } = props;

  const store = useStore();
  const shift = store.scheduleStore.shifts[shiftId];

  const [errors, setErrors] = useState<{ [key: string]: string[] }>({});

  const [rotationName, setRotationName] = useState<string>(`[L${layerPriority}] Rotation`);
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [offsetTop, setOffsetTop] = useState<number>(0);

  const [shiftStart, setShiftStart] = useState<dayjs.Dayjs>(propsShiftStart);
  const [shiftEnd, setShiftEnd] = useState<dayjs.Dayjs>(propsShiftEnd || shiftStart.add(1, 'day'));
  const [activePeriod, setActivePeriod] = useState<number | undefined>(undefined);
  const [shiftPeriodDefaultValue, setShiftPeriodDefaultValue] = useState<number | undefined>(undefined);

  const [rotationStart, setRotationStart] = useState<dayjs.Dayjs>(shiftStart);
  const [endLess, setEndless] = useState<boolean>(true);
  const [rotationEnd, setRotationEnd] = useState<dayjs.Dayjs>(shiftStart.add(1, 'month'));

  const [repeatEveryValue, setRepeatEveryValue] = useState<number>(1);
  const [repeatEveryPeriod, setRepeatEveryPeriod] = useState<RepeatEveryPeriod>(RepeatEveryPeriod.DAYS);

  const [showActiveOnSelectedDays, setShowActiveOnSelectedDays] = useState<boolean>(false);
  const [showActiveOnSelectedPartOfDay, setShowActiveOnSelectedPartOfDay] = useState<boolean>(false);

  const [selectedDays, setSelectedDays] = useState<string[]>([]);

  const [userGroups, setUserGroups] = useState([]);

  const [showDeleteRotationConfirmation, setShowDeleteRotationConfirmation] = useState<boolean>(false);

  useEffect(() => {
    if (rotationStart.isBefore(shiftStart)) {
      setRotationStart(shiftStart);
    }
  }, [rotationStart, shiftStart]);

  useEffect(() => {
    if (!showActiveOnSelectedDays) {
      setSelectedDays([]);
    }
  }, [showActiveOnSelectedDays]);

  useEffect(() => {
    if (isOpen) {
      waitForElement(`#layer${shiftId === 'new' ? layerPriority : shift?.priority_level}`).then((elm) => {
        const modal = document.querySelector(`.${cx('draggable')}`) as HTMLDivElement;
        const coords = getCoords(elm);

        const offsetTop = Math.max(
          Math.min(coords.top - modal?.offsetHeight - 10, document.body.offsetHeight - modal?.offsetHeight - 10),
          GRAFANA_HEADER_HEIGHT + 10
        );

        setOffsetTop(offsetTop);
      });
    }
  }, [isOpen]);

  const handleChangeEndless = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      setEndless(!event.currentTarget.checked);
    },
    [endLess]
  );

  const handleDeleteClick = useCallback((force: boolean) => {
    store.scheduleStore.deleteOncallShift(shiftId, force).then(() => {
      onDelete();
    });
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

  const updatePreview = () => {
    setErrors({});

    store.scheduleStore
      .updateRotationPreview(scheduleId, shiftId, startMoment, false, params)
      .catch(onError)
      .finally(() => {
        setIsOpen(true);
      });
  };

  const onError = useCallback((error) => {
    setErrors(error.response.data);
  }, []);

  const handleChange = useDebouncedCallback(updatePreview, 200);

  const params = useMemo(
    () => ({
      rotation_start: getUTCString(rotationStart),
      until: endLess ? null : getUTCString(rotationEnd),
      shift_start: getUTCString(shiftStart),
      shift_end: getUTCString(shiftEnd),
      rolling_users: userGroups,
      interval: repeatEveryValue,
      frequency: repeatEveryPeriod,
      by_day: getUTCByDay(store.scheduleStore.byDayOptions, selectedDays, shiftStart.tz(currentTimezone)),
      week_start: getUTCWeekStart(store.scheduleStore.byDayOptions, shiftStart.tz(currentTimezone)),
      priority_level: shiftId === 'new' ? layerPriority : shift?.priority_level,
      name: rotationName,
    }),
    [
      rotationStart,
      currentTimezone,
      rotationEnd,
      shiftStart,
      shiftEnd,
      userGroups,
      repeatEveryValue,
      repeatEveryPeriod,
      selectedDays,
      shiftId,
      layerPriority,
      shift,
      endLess,
      rotationName,
    ]
  );

  useEffect(handleChange, [params, startMoment]);

  const create = useCallback(() => {
    store.scheduleStore
      .createRotation(scheduleId, false, { ...params, name: rotationName })
      .then(() => {
        onCreate();
      })
      .catch(onError);
  }, [scheduleId, shiftId, params]);

  const update = useCallback(() => {
    store.scheduleStore
      .updateRotation(shiftId, params)
      .then(() => {
        onUpdate();
      })
      .catch(onError);
  }, [shiftId, params]);

  const updateAsNew = useCallback(() => {
    store.scheduleStore
      .updateRotationAsNew(shiftId, params)
      .then(() => {
        onUpdate();
      })
      .catch(onError);
  }, [shiftId, params]);

  const handleEditNewerRotationClick = useCallback(() => {
    onShowRotationForm(shift.updated_shift);
  }, [shift?.updated_shift]);

  const handleRepeatEveryPeriodChange = useCallback(
    (value) => {
      setShiftPeriodDefaultValue(undefined);

      setRepeatEveryPeriod(value);

      if (!showActiveOnSelectedPartOfDay) {
        if (showActiveOnSelectedDays) {
          setShiftEnd(shiftStart.add(24, 'hours'));
        } else {
          setShiftEnd(shiftStart.add(repeatEveryValue, repeatEveryPeriodToUnitName[value]));
        }
      }
    },
    [showActiveOnSelectedPartOfDay, showActiveOnSelectedDays, repeatEveryValue]
  );

  const handleRepeatEveryValueChange = useCallback(
    (option) => {
      const value = Math.floor(Number(option.value));
      if (isNaN(value) || value < 1) {
        return;
      }

      setShiftPeriodDefaultValue(undefined);
      setRepeatEveryValue(value);

      if (!showActiveOnSelectedPartOfDay) {
        setShiftEnd(shiftStart.add(value, repeatEveryPeriodToUnitName[repeatEveryPeriod]));
      }
    },
    [showActiveOnSelectedPartOfDay, repeatEveryPeriod]
  );

  const handleRotationStartChange = useCallback(
    (value) => {
      setRotationStart(value);
      setShiftStart(value);
      if (showActiveOnSelectedPartOfDay) {
        setShiftEnd(value.add(activePeriod, 'seconds'));
      } else {
        setShiftEnd(value.add(repeatEveryValue, repeatEveryPeriodToUnitName[repeatEveryPeriod]));
      }
    },
    [showActiveOnSelectedPartOfDay, activePeriod, repeatEveryPeriod, repeatEveryValue]
  );

  const handleActivePeriodChange = useCallback(
    (value) => {
      setActivePeriod(value);
      setShiftEnd(shiftStart.add(value, 'seconds'));
    },
    [shiftStart]
  );

  const handleRotationNameChange = useCallback(
    (name: string) => {
      setRotationName(name);
    },
    [shiftId, params, shift]
  );

  const handleShowActiveOnSelectedDaysToggle = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const value = event.currentTarget.checked;

      setShowActiveOnSelectedDays(value);

      if (value) {
        setShiftEnd(shiftStart.add(24, 'hours'));
      } else {
        if (!showActiveOnSelectedPartOfDay) {
          setShiftEnd(shiftStart.add(repeatEveryValue, repeatEveryPeriodToUnitName[repeatEveryPeriod]));
        }
      }
    },
    [showActiveOnSelectedPartOfDay, shiftStart, repeatEveryValue, repeatEveryPeriod]
  );

  const handleShowActiveOnSelectedPartOfDayToggle = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const value = event.currentTarget.checked;
      setShowActiveOnSelectedPartOfDay(value);

      if (!value) {
        if (showActiveOnSelectedPartOfDay) {
          setShiftEnd(shiftStart.add(24, 'hours'));
        } else {
          setShiftEnd(shiftStart.add(repeatEveryValue, repeatEveryPeriodToUnitName[repeatEveryPeriod]));
        }
      }
    },
    [shiftStart, repeatEveryPeriod, repeatEveryValue, showActiveOnSelectedPartOfDay]
  );

  useEffect(() => {
    if (repeatEveryPeriod === RepeatEveryPeriod.MONTHS) {
      setShowActiveOnSelectedPartOfDay(false);
    }
  }, [repeatEveryPeriod]);

  useEffect(() => {
    if (shift) {
      setRotationName(getShiftName(shift));
      const shiftStart = getDateTime(shift.shift_start);
      // use shiftStart as rotationStart for existing shifts
      // (original rotationStart defaulted to the shift creation timestamp)
      setRotationStart(shiftStart);
      setRotationEnd(shift.until ? getDateTime(shift.until) : getDateTime(shift.shift_start).add(1, 'month'));
      setShiftStart(shiftStart);
      const shiftEnd = getDateTime(shift.shift_end);
      setShiftEnd(shiftEnd);
      setEndless(!shift.until);

      setRepeatEveryValue(shift.interval);
      setRepeatEveryPeriod(shift.frequency);
      setSelectedDays(getSelectedDays(store.scheduleStore.byDayOptions, shift.by_day, shiftStart.tz(currentTimezone)));

      setShowActiveOnSelectedDays(Boolean(shift.by_day?.length));

      const activeOnSelectedPartOfDay =
        repeatEveryInSeconds(shift.frequency, shift.interval) !== shiftEnd.diff(shiftStart, 'seconds');

      setShowActiveOnSelectedPartOfDay(activeOnSelectedPartOfDay);
      if (activeOnSelectedPartOfDay) {
        const activePeriod = shiftEnd.diff(shiftStart, 'seconds');

        setActivePeriod(activePeriod);
        setShiftPeriodDefaultValue(activePeriod);
      }

      setUserGroups(shift.rolling_users);
    }
  }, [shift]);

  useEffect(() => {
    if (shift) {
      setSelectedDays(getSelectedDays(store.scheduleStore.byDayOptions, shift.by_day, shiftStart.tz(currentTimezone)));
    }
  }, [currentTimezone]);

  const isFormValid = useMemo(() => !Object.keys(errors).length, [errors]);

  const hasUpdatedShift = shift && shift.updated_shift;
  const ended = shift && shift.until && getDateTime(shift.until).isBefore(dayjs());

  const disabled = hasUpdatedShift || ended;

  return (
    <>
      <Modal
        top="0"
        isOpen={isOpen}
        width="430px"
        onDismiss={onHide}
        contentElement={(props, children) => (
          <Draggable handle=".drag-handler" defaultClassName={cx('draggable')} positionOffset={{ x: 0, y: offsetTop }}>
            <div {...props}>{children}</div>
          </Draggable>
        )}
      >
        <div className={cx('root')}>
          <div>
            <HorizontalGroup justify="space-between">
              <HorizontalGroup spacing="sm">
                {shiftId === 'new' && <Tag color={shiftColor}>New</Tag>}
                <Text.Title editModalTitle="Rotation name" onTextChange={handleRotationNameChange} level={5} editable>
                  {rotationName}
                </Text.Title>
              </HorizontalGroup>
              <HorizontalGroup>
                {shiftId !== 'new' && (
                  <IconButton
                    variant="secondary"
                    tooltip="Delete"
                    name="trash-alt"
                    onClick={() => setShowDeleteRotationConfirmation(true)}
                  />
                )}
                <IconButton variant="secondary" className={cx('drag-handler')} name="draggabledots" />
                <IconButton
                  name="times"
                  variant="secondary"
                  tooltip={shiftId === 'new' ? 'Cancel' : 'Close'}
                  onClick={onHide}
                />
              </HorizontalGroup>
            </HorizontalGroup>
          </div>
          <div className={cx('body')}>
            <div className={cx('content')}>
              <VerticalGroup spacing="none">
                {hasUpdatedShift && (
                  <Block bordered className={cx('updated-shift-info')}>
                    <VerticalGroup>
                      <HorizontalGroup align="flex-start">
                        <Icon name="info-circle" size="md"></Icon>
                        <Text>
                          This rotation is read-only because it has newer version.{' '}
                          <Text onClick={handleEditNewerRotationClick} type="link" clickable>
                            Edit the newer version
                          </Text>{' '}
                          instead
                        </Text>
                      </HorizontalGroup>
                    </VerticalGroup>
                  </Block>
                )}
                {!hasUpdatedShift && ended && (
                  <Block bordered className={cx('updated-shift-info')}>
                    <VerticalGroup>
                      <HorizontalGroup>
                        <Icon name="info-circle" size="md"></Icon>
                        <Text>This rotation is over</Text>
                      </HorizontalGroup>
                    </VerticalGroup>
                  </Block>
                )}
                <div className={cx('two-fields')}>
                  <Field
                    label={
                      <Text type="primary" size="small">
                        Starts
                      </Text>
                    }
                  >
                    <DateTimePicker
                      //minMoment={shiftStart}
                      value={rotationStart}
                      onChange={handleRotationStartChange}
                      timezone={currentTimezone}
                      error={errors.rotation_start}
                      disabled={disabled}
                    />
                  </Field>
                  <Field
                    label={
                      <HorizontalGroup spacing="xs">
                        <Text type="primary" size="small">
                          Ends
                        </Text>
                        <InlineSwitch
                          className={cx('inline-switch')}
                          transparent
                          value={!endLess}
                          onChange={handleChangeEndless}
                          disabled={disabled}
                        />
                      </HorizontalGroup>
                    }
                  >
                    {endLess ? (
                      <div style={{ lineHeight: '32px' }}>
                        <Text type="secondary">Endless</Text>
                      </div>
                    ) : (
                      <DateTimePicker
                        value={rotationEnd}
                        onChange={setRotationEnd}
                        timezone={currentTimezone}
                        error={errors.until}
                        disabled={disabled}
                      />
                    )}
                  </Field>
                </div>
                <div className={cx('two-fields')}>
                  <Field
                    invalid={Boolean(errors.interval)}
                    error={'Invalid recurrence period'}
                    label={
                      <HorizontalGroup spacing="sm">
                        <Text type="primary" size="small">
                          Recurrence period
                        </Text>
                        <Tooltip content="Time interval when users shifts are rotated. Shifts active period can be customised by days of the week and hours during a day.">
                          <Icon name="info-circle" size="md"></Icon>
                        </Tooltip>
                      </HorizontalGroup>
                    }
                  >
                    <Select
                      maxMenuHeight={120}
                      value={repeatEveryValue}
                      options={getRepeatShiftsEveryOptions(repeatEveryPeriod)}
                      onChange={handleRepeatEveryValueChange}
                      disabled={disabled}
                      allowCustomValue
                    />
                  </Field>
                  <Field label="">
                    <RemoteSelect
                      showSearch={false}
                      href="/oncall_shifts/frequency_options/"
                      value={repeatEveryPeriod}
                      onChange={handleRepeatEveryPeriodChange}
                      disabled={disabled}
                    />
                  </Field>
                </div>
                <VerticalGroup spacing="md">
                  <VerticalGroup>
                    <HorizontalGroup align="flex-start">
                      <Switch
                        disabled={disabled}
                        value={showActiveOnSelectedDays}
                        onChange={handleShowActiveOnSelectedDaysToggle}
                      />
                      <VerticalGroup>
                        <Text type="secondary">Mask by weekdays</Text>
                        {showActiveOnSelectedDays && (
                          <DaysSelector
                            options={store.scheduleStore.byDayOptions}
                            value={selectedDays}
                            onChange={setSelectedDays}
                            weekStart={getWeekStartString()}
                            disabled={disabled}
                          />
                        )}
                      </VerticalGroup>
                    </HorizontalGroup>

                    <HorizontalGroup align="flex-start">
                      <Switch
                        disabled={disabled || repeatEveryPeriod === RepeatEveryPeriod.MONTHS}
                        value={showActiveOnSelectedPartOfDay}
                        onChange={handleShowActiveOnSelectedPartOfDayToggle}
                      />
                      <VerticalGroup>
                        <Text type="secondary">Limit each shift length</Text>
                        {showActiveOnSelectedPartOfDay && (
                          <ShiftPeriod
                            repeatEveryPeriod={showActiveOnSelectedDays ? RepeatEveryPeriod.HOURS : repeatEveryPeriod}
                            repeatEveryValue={
                              showActiveOnSelectedDays
                                ? repeatEveryPeriod === RepeatEveryPeriod.HOURS
                                  ? Math.min(repeatEveryValue, 24)
                                  : 24
                                : repeatEveryValue
                            }
                            defaultValue={shiftPeriodDefaultValue}
                            shiftStart={shiftStart}
                            onChange={handleActivePeriodChange}
                            currentTimezone={currentTimezone}
                            disabled={disabled}
                            errors={errors}
                          />
                        )}
                        {showActiveOnSelectedDays && (
                          <Text type="secondary">
                            Since masking by weekdays is enabled shift length is limited to 24h and shift will repeat
                            every day
                          </Text>
                        )}
                      </VerticalGroup>
                    </HorizontalGroup>
                  </VerticalGroup>
                </VerticalGroup>
                <div style={{ marginTop: '16px' }}>
                  <HorizontalGroup>
                    <Text size="small">Users</Text>
                    <Tooltip content="By default each new user creates new rotation group. You can customise groups by dragging.">
                      <Icon name="info-circle" size="md" />
                    </Tooltip>
                  </HorizontalGroup>
                </div>
                <UserGroups
                  disabled={disabled}
                  value={userGroups}
                  onChange={setUserGroups}
                  isMultipleGroups={true}
                  renderUser={(pk: User['pk']) => (
                    <UserItem
                      pk={pk}
                      shiftColor={shiftColor}
                      shiftStart={params.shift_start}
                      shiftEnd={params.shift_end}
                    />
                  )}
                  showError={Boolean(errors.rolling_users)}
                />
              </VerticalGroup>
            </div>
          </div>
          <div>
            <HorizontalGroup justify="space-between">
              <Text type="secondary">Current timezone: {getTzOffsetString(dayjs().tz(currentTimezone))}</Text>
              <HorizontalGroup>
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
              </HorizontalGroup>
            </HorizontalGroup>
          </div>
        </div>
      </Modal>
      {showDeleteRotationConfirmation && (
        <DeletionModal onHide={() => setShowDeleteRotationConfirmation(false)} onConfirm={handleDeleteClick} />
      )}
    </>
  );
});

interface ShiftPeriodProps {
  repeatEveryPeriod: number;
  repeatEveryValue: number;
  defaultValue: number;
  shiftStart: dayjs.Dayjs;
  onChange: (value: number) => void;
  currentTimezone: Timezone;
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
    <VerticalGroup>
      {timeUnits.map((unit, index: number, arr) => (
        <HorizontalGroup key={unit.unit}>
          <TimeUnitSelector
            disabled={disabled}
            unit={unit.unit}
            value={unit.value}
            onChange={getTimeUnitChangeHandler(unit.unit)}
            maxValue={unit.maxValue}
            className={cx('time-unit')}
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
        </HorizontalGroup>
      ))}
      {timeUnits.length === 0 && unitToCreate !== undefined && (
        <Button disabled={disabled} variant="secondary" icon="plus" size="sm" onClick={handleTimeUnitAdd}>
          Add time segment
        </Button>
      )}
      <Text type="secondary">({duration || '0m'})</Text>
      {errors.shift_end && <Text type="danger">Shift length must be greater than zero</Text>}
    </VerticalGroup>
  );
};

export default RotationForm;
