import React, { useCallback, useEffect, useMemo, useState } from 'react';

import { config } from '@grafana/runtime';
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

import Collapse from 'components/Collapse/Collapse';
import Modal from 'components/Modal/Modal';
import Tag from 'components/Tag/Tag';
import Text from 'components/Text/Text';
import UserGroups from 'components/UserGroups/UserGroups';
import RemoteSelect from 'containers/RemoteSelect/RemoteSelect';
import {
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
import { getFromString, getShiftTitle } from 'models/schedule/schedule.helpers';
import { Schedule, Shift } from 'models/schedule/schedule.types';
import { getTzOffsetString } from 'models/timezone/timezone.helpers';
import { Timezone } from 'models/timezone/timezone.types';
import { User } from 'models/user/user.types';
import { getDateTime, getStartOfWeek, getUTCByDay, getUTCString } from 'pages/schedule/Schedule.helpers';
import { useStore } from 'state/useStore';
import { getCoords, waitForElement } from 'utils/DOM';
import { GRAFANA_HEADER_HEIGTH } from 'utils/consts';
import { useDebouncedCallback } from 'utils/hooks';

import { getRepeatShiftsEveryOptions } from './RotationForm2.helpers';

import styles from './RotationForm2.module.css';

const cx = cn.bind(styles);

interface RotationForm2Props {
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
}

const RotationForm2 = observer((props: RotationForm2Props) => {
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
  } = props;

  const store = useStore();
  const shift = store.scheduleStore.shifts[shiftId];

  const [errors, setErrors] = useState<{ [key: string]: string[] }>({});

  const [rotationTitle, setRotationTitle] = useState<string>(`[L${layerPriority}] Rotation`);
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [offsetTop, setOffsetTop] = useState<number>(0);

  const [shiftStart, setShiftStart] = useState<dayjs.Dayjs>(propsShiftStart);
  const [shiftEnd, setShiftEnd] = useState<dayjs.Dayjs>(propsShiftEnd || shiftStart.add(1, 'day'));
  const [shiftPeriodDefaultValue, setShiftPeriodDefaultValue] = useState<number | undefined>(undefined);

  const [rotationStart, setRotationStart] = useState<dayjs.Dayjs>(shiftStart);
  const [endLess, setEndless] = useState<boolean>(true);
  const [rotationEnd, setRotationEnd] = useState<dayjs.Dayjs>(shiftStart.add(1, 'month'));

  const [repeatEveryValue, setRepeatEveryValue] = useState<number>(1);
  const [repeatEveryPeriod, setRepeatEveryPeriod] = useState<number>(0);

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
    if (!showActiveOnSelectedPartOfDay) {
      setShiftEnd(propsShiftStart.add(repeatEveryValue, repeatEveryPeriodToUnitName[repeatEveryPeriod]));
    }
  }, [showActiveOnSelectedPartOfDay]);

  useEffect(() => {
    if (isOpen) {
      waitForElement(`#layer${shiftId === 'new' ? layerPriority : shift?.priority_level}`).then((elm) => {
        const modal = document.querySelector(`.${cx('draggable')}`) as HTMLDivElement;
        const coords = getCoords(elm);

        const offsetTop = Math.max(
          Math.min(coords.top - modal?.offsetHeight - 10, document.body.offsetHeight - modal?.offsetHeight - 10),
          GRAFANA_HEADER_HEIGTH + 10
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
      .updateRotationPreview(scheduleId, shiftId, getFromString(startMoment), false, params)
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
      by_day: getUTCByDay(store.scheduleStore.byDayOptions, selectedDays, shiftStart),
      /*  repeatEveryPeriod === 0 || repeatEveryPeriod === 1
          ? getUTCByDay(store.scheduleStore.byDayOptions, selectedDays, shiftStart)
          : null, */
      priority_level: shiftId === 'new' ? layerPriority : shift?.priority_level,
      title: rotationTitle,
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
      rotationTitle,
    ]
  );

  useEffect(handleChange, [params]);

  const handleCreate = useCallback(() => {
    if (shiftId === 'new') {
      store.scheduleStore
        .createRotation(scheduleId, false, { ...params, title: rotationTitle })
        .then(() => {
          onCreate();
        })
        .catch(onError);
    } else {
      store.scheduleStore
        .updateRotation(shiftId, params)
        .then(() => {
          onUpdate();
        })
        .catch(onError);
    }
  }, [scheduleId, shiftId, params]);

  const handleRepeatEveryPeriodChange = useCallback(
    (value) => {
      setShiftPeriodDefaultValue(undefined);

      setRepeatEveryPeriod(value);

      if (!showActiveOnSelectedPartOfDay) {
        setShiftEnd(shiftStart.add(repeatEveryValue, repeatEveryPeriodToUnitName[value]));
      }
    },
    [showActiveOnSelectedPartOfDay, repeatEveryValue]
  );

  const handleRepeatEveryValueChange = useCallback(
    (option) => {
      setShiftPeriodDefaultValue(undefined);

      const value = Number(option.value);
      setRepeatEveryValue(value);

      if (!showActiveOnSelectedPartOfDay) {
        setShiftEnd(shiftStart.add(value, repeatEveryPeriodToUnitName[repeatEveryPeriod]));
      }
    },
    [showActiveOnSelectedPartOfDay, repeatEveryPeriod]
  );

  const handleRotationTitleChange = useCallback(
    (title: string) => {
      setRotationTitle(title);
      if (shiftId !== 'new') {
        store.scheduleStore.updateRotation(shiftId, { ...params, title }).catch((error) => {
          if (error.response?.data?.title) {
            setRotationTitle(getShiftTitle(shift));
          }
        });
      }
    },
    [shiftId, params, shift]
  );

  const handleShowActiveOnSelectedDaysToggle = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    setShowActiveOnSelectedDays(event.currentTarget.checked);
  }, []);

  const handleShowActiveOnSelectedPartOfDayToggle = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    setShowActiveOnSelectedPartOfDay(event.currentTarget.checked);
  }, []);

  useEffect(() => {
    if (repeatEveryPeriod === RepeatEveryPeriod.MONTHS) {
      setShowActiveOnSelectedPartOfDay(false);
    }
  }, [repeatEveryPeriod]);

  useEffect(() => {
    if (shift) {
      setRotationTitle(getShiftTitle(shift));
      setRotationStart(getDateTime(shift.rotation_start));
      setRotationEnd(shift.until ? getDateTime(shift.until) : getDateTime(shift.shift_start).add(1, 'month'));
      const shiftStart = getDateTime(shift.shift_start);
      setShiftStart(shiftStart);
      const shiftEnd = getDateTime(shift.shift_end);
      setShiftEnd(shiftEnd);
      setEndless(!shift.until);

      setRepeatEveryValue(shift.interval);
      setRepeatEveryPeriod(shift.frequency);
      setSelectedDays(shift.by_day || []);

      setShowActiveOnSelectedDays(Boolean(shift.by_day?.length));

      const activeOnSelectedPartOfDay =
        repeatEveryInSeconds(shift.frequency, shift.interval) !== shiftEnd.diff(shiftStart, 'seconds');

      setShowActiveOnSelectedPartOfDay(activeOnSelectedPartOfDay);
      if (activeOnSelectedPartOfDay) {
        setShiftPeriodDefaultValue(shiftEnd.diff(shiftStart, 'seconds'));
      }

      setUserGroups(shift.rolling_users);
    }
  }, [shift]);

  const isFormValid = useMemo(() => !Object.keys(errors).length, [errors]);

  return (
    <>
      <Modal
        top="0"
        isOpen={isOpen}
        className={cx('modal')}
        width="430px"
        onDismiss={onHide}
        contentElement={(props, children) => (
          <Draggable handle=".drag-handler" defaultClassName={cx('draggable')} positionOffset={{ x: 0, y: offsetTop }}>
            <div {...props}>{children}</div>
          </Draggable>
        )}
      >
        <div className={cx('root')}>
          <div className={cx('header')}>
            <HorizontalGroup justify="space-between">
              <HorizontalGroup spacing="sm">
                {shiftId === 'new' && <Tag color={shiftColor}>New</Tag>}
                <Text.Title editModalTitle="Rotation name" onTextChange={handleRotationTitleChange} level={5} editable>
                  {rotationTitle}
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
              </HorizontalGroup>
            </HorizontalGroup>
          </div>
          <div className={cx('body')}>
            <div className={cx('content')}>
              <VerticalGroup spacing="none">
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
                      onChange={setRotationStart}
                      timezone={currentTimezone}
                      error={errors.rotation_start}
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
                      />
                    )}
                  </Field>
                </div>
                <div className={cx('two-fields')}>
                  <Field
                    label={
                      <HorizontalGroup spacing="sm">
                        <Text type="primary" size="small">
                          Rotate shifts every
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
                      allowCustomValue
                    />
                  </Field>
                  <Field label="">
                    <RemoteSelect
                      href="/oncall_shifts/frequency_options/"
                      value={repeatEveryPeriod}
                      onChange={handleRepeatEveryPeriodChange}
                    />
                  </Field>
                </div>

                <Collapse
                  className={cx('active-periods')}
                  contentClassName={cx('active-periods-content')}
                  isOpen={shiftId !== 'new'}
                  label={<Text>Active period</Text>}
                >
                  <VerticalGroup spacing="md">
                    <VerticalGroup>
                      <HorizontalGroup align="flex-start">
                        <Switch value={showActiveOnSelectedDays} onChange={handleShowActiveOnSelectedDaysToggle} />
                        <VerticalGroup>
                          <Text type="secondary">Active on selected days</Text>
                          {showActiveOnSelectedDays && (
                            <DaysSelector
                              options={store.scheduleStore.byDayOptions}
                              value={selectedDays}
                              onChange={setSelectedDays}
                              weekStart={config.bootData.user.weekStart}
                            />
                          )}
                        </VerticalGroup>
                      </HorizontalGroup>

                      <HorizontalGroup align="flex-start">
                        <Switch
                          disabled={repeatEveryPeriod === RepeatEveryPeriod.MONTHS}
                          value={showActiveOnSelectedPartOfDay}
                          onChange={handleShowActiveOnSelectedPartOfDayToggle}
                        />
                        <VerticalGroup>
                          <Text type="secondary">Active on selected part</Text>
                          {showActiveOnSelectedPartOfDay && (
                            <ShiftPeriod
                              repeatEveryPeriod={repeatEveryPeriod}
                              repeatEveryValue={repeatEveryValue}
                              defaultValue={shiftPeriodDefaultValue}
                              shiftStart={shiftStart}
                              onShiftEndChange={setShiftEnd}
                              currentTimezone={currentTimezone}
                              errors={errors}
                            />
                          )}
                        </VerticalGroup>
                      </HorizontalGroup>
                    </VerticalGroup>
                  </VerticalGroup>
                </Collapse>
                <div style={{ marginTop: '16px' }}>
                  <HorizontalGroup>
                    <Text size="small">Users</Text>
                    <Tooltip content="By default each new user creates new rotation group. You can customise groups by dragging.">
                      <Icon name="info-circle" size="md" />
                    </Tooltip>
                  </HorizontalGroup>
                </div>
                <UserGroups
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
          <div className={cx('footer')}>
            <HorizontalGroup justify="space-between">
              <Text type="secondary">Current timezone: {getTzOffsetString(dayjs().tz(currentTimezone))}</Text>
              <HorizontalGroup>
                <Button variant="secondary" onClick={onHide}>
                  {shiftId === 'new' ? 'Cancel' : 'Close'}
                </Button>
                <Button variant="primary" onClick={handleCreate} disabled={!isFormValid}>
                  {shiftId === 'new' ? 'Create' : 'Update'}
                </Button>
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
  onShiftEndChange: (moment: dayjs.Dayjs) => void;
  currentTimezone: Timezone;
  errors: any;
}

const ShiftPeriod = ({
  repeatEveryPeriod,
  repeatEveryValue,
  defaultValue,
  shiftStart,
  onShiftEndChange,
  errors,
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
    const newShiftEnd = shiftStart.add(timeUnitsToSeconds(timeUnits), 'seconds');

    onShiftEndChange(newShiftEnd);
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
            unit={unit.unit}
            value={unit.value}
            onChange={getTimeUnitChangeHandler(unit.unit)}
            maxValue={unit.maxValue}
            className={cx('time-unit')}
          />
          {index === arr.length - 1 && (
            <Button
              tooltip="Remove segment"
              variant="secondary"
              icon="times"
              size="sm"
              onClick={getTimeUnitDeleteHandler(unit.unit)}
            />
          )}
          {index === arr.length - 1 && unitToCreate !== undefined && (
            <Button tooltip="Add segment" variant="secondary" icon="plus" size="sm" onClick={handleTimeUnitAdd} />
          )}
        </HorizontalGroup>
      ))}
      {timeUnits.length === 0 && unitToCreate !== undefined && (
        <Button variant="secondary" icon="plus" size="sm" onClick={handleTimeUnitAdd}>
          Add segment
        </Button>
      )}
      <Text type="secondary">({duration || '0m'})</Text>
      {errors.shift_end && <Text type="danger">Incorrect active period</Text>}
    </VerticalGroup>
  );
};

export default RotationForm2;
