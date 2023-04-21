import React, { useCallback, useEffect, useMemo, useState } from 'react';

import { config } from '@grafana/runtime';
import {
  Button,
  Field,
  HorizontalGroup,
  Icon,
  IconButton,
  InlineSwitch,
  RadioButtonGroup,
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
import DateTimePicker from 'containers/RotationForm/parts/DateTimePicker';
import DaysSelector from 'containers/RotationForm/parts/DaysSelector';
import DeletionModal from 'containers/RotationForm/parts/DeletionModal';
import UserItem from 'containers/RotationForm/parts/UserItem';
import WeekdayTimePicker from 'containers/RotationForm/parts/WeekdayTimePicker';
import { getFromString, getShiftTitle } from 'models/schedule/schedule.helpers';
import { Schedule, Shift } from 'models/schedule/schedule.types';
import { getTzOffsetString } from 'models/timezone/timezone.helpers';
import { Timezone } from 'models/timezone/timezone.types';
import { User } from 'models/user/user.types';
import { getDateTime, getStartOfWeek, getUTCByDay, getUTCString } from 'pages/schedule/Schedule.helpers';
import { useStore } from 'state/useStore';
import { getCoords, waitForElement } from 'utils/DOM';
import { GRAFANA_HEADER_HEIGTH } from 'utils/consts';
import { toHHmmss } from 'utils/datetime';
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

enum Mode {
  'SELECTED_DAYS_AND_HOURS' = '0',
  'CUSTOM_TIME_INTERVAL' = '1',
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

  const [rotationTitle, setRotationTitle] = useState<string>(`[L${layerPriority}] Rotation`);
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [offsetTop, setOffsetTop] = useState<number>(0);

  const [shiftStart, setShiftStart] = useState<dayjs.Dayjs>(propsShiftStart);
  const [shiftEnd, setShiftEnd] = useState<dayjs.Dayjs>(propsShiftEnd || shiftStart.add(1, 'day'));

  const [rotationStart, setRotationStart] = useState<dayjs.Dayjs>(shiftStart);
  const [endLess, setEndless] = useState<boolean>(true);
  const [rotationEnd, setRotationEnd] = useState<dayjs.Dayjs>(shiftStart.add(1, 'month'));

  const [repeatEveryValue, setRepeatEveryValue] = useState<number>(1);
  const [repeatEveryPeriod, setRepeatEveryPeriod] = useState<number>(0);

  const withinOneDay = useMemo(
    () => shiftStart.tz(currentTimezone).isSame(shiftEnd.tz(currentTimezone).subtract(1, 'millisecond'), 'day'),
    [shiftStart, shiftEnd, currentTimezone]
  );

  const [mode, setMode] = useState<Mode>(withinOneDay ? Mode.SELECTED_DAYS_AND_HOURS : Mode.CUSTOM_TIME_INTERVAL);
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
    if (showActiveOnSelectedPartOfDay) {
      setShiftStart(propsShiftStart);
      setShiftEnd(propsShiftStart.add(12, 'hour'));
    } else {
      setShiftStart(propsShiftStart);
      setShiftEnd(propsShiftStart.add(1, 'day'));
    }
  }, [showActiveOnSelectedPartOfDay]);

  useEffect(() => {
    if (mode === Mode.SELECTED_DAYS_AND_HOURS) {
      if (!withinOneDay) {
        setShiftStart(propsShiftStart);
        setShiftEnd(propsShiftStart.add(1, 'day'));
      } else {
        setShowActiveOnSelectedDays(false);
        setShowActiveOnSelectedPartOfDay(false);
      }
    }
  }, [mode]);

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
    store.scheduleStore
      .updateRotationPreview(scheduleId, shiftId, getFromString(startMoment), false, params)
      .finally(() => {
        setIsOpen(true);
      });
  };

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
      by_day:
        repeatEveryPeriod === 0 || repeatEveryPeriod === 1
          ? getUTCByDay(store.scheduleStore.byDayOptions, selectedDays, shiftStart)
          : null,
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
      store.scheduleStore.createRotation(scheduleId, false, { ...params, title: rotationTitle }).then(() => {
        onCreate();
      });
    } else {
      store.scheduleStore.updateRotation(shiftId, params).then(() => {
        onUpdate();
      });
    }
  }, [scheduleId, shiftId, params]);

  const handleRepeatEveryValueChange = useCallback((option) => {
    setRepeatEveryValue(Number(option.value));
  }, []);

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
    if (shift) {
      setRotationTitle(getShiftTitle(shift));
      setRotationStart(getDateTime(shift.rotation_start));
      setRotationEnd(shift.until ? getDateTime(shift.until) : getDateTime(shift.shift_start).add(1, 'month'));
      setShiftStart(getDateTime(shift.shift_start));
      setShiftEnd(getDateTime(shift.shift_end));
      setEndless(!shift.until);

      setRepeatEveryValue(shift.interval);
      setRepeatEveryPeriod(shift.frequency);
      setSelectedDays(shift.by_day || []);

      setUserGroups(shift.rolling_users);
    }
  }, [shift]);

  const isFormValid = useMemo(() => userGroups.some((group) => group.length), [userGroups]);
  const disableAction = !endLess && rotationEnd.isBefore(dayjs().tz(currentTimezone));

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
                      minMoment={shiftStart}
                      value={rotationStart}
                      onChange={setRotationStart}
                      timezone={currentTimezone}
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
                      <DateTimePicker value={rotationEnd} onChange={setRotationEnd} timezone={currentTimezone} />
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
                      onChange={setRepeatEveryPeriod}
                    />
                  </Field>
                </div>
                <Collapse
                  className={cx('active-periods')}
                  contentClassName={cx('active-periods-content')}
                  isOpen={false}
                  label={<Text>Weekly active periods</Text>}
                >
                  <VerticalGroup spacing="md">
                    <RadioButtonGroup
                      options={[
                        {
                          label: 'Selected days and hours',
                          value: Mode.SELECTED_DAYS_AND_HOURS,
                        },
                        { label: 'Custom time interval', value: Mode.CUSTOM_TIME_INTERVAL },
                      ]}
                      value={mode}
                      onChange={setMode}
                    />

                    {mode === Mode.SELECTED_DAYS_AND_HOURS && (
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
                            value={showActiveOnSelectedPartOfDay}
                            onChange={handleShowActiveOnSelectedPartOfDayToggle}
                          />
                          <VerticalGroup>
                            <Text type="secondary">Active on selected part of the day</Text>
                            {showActiveOnSelectedPartOfDay && (
                              <ShiftPeriod
                                hideWeekday
                                shiftStart={shiftStart}
                                shiftEnd={shiftEnd}
                                setShiftStart={setShiftStart}
                                setShiftEnd={setShiftEnd}
                                currentTimezone={currentTimezone}
                              />
                            )}
                          </VerticalGroup>
                        </HorizontalGroup>
                      </VerticalGroup>
                    )}

                    {mode === Mode.CUSTOM_TIME_INTERVAL && (
                      <ShiftPeriod
                        hideWeekday={false}
                        shiftStart={shiftStart}
                        shiftEnd={shiftEnd}
                        setShiftStart={setShiftStart}
                        setShiftEnd={setShiftEnd}
                        currentTimezone={currentTimezone}
                      />
                    )}
                  </VerticalGroup>
                </Collapse>
                <div style={{ marginTop: '16px' }}>
                  <HorizontalGroup>
                    <Text size="small">Users</Text>
                    <Tooltip content="By default each new user creates new rotation group. You can customise groups by dragging.">
                      <Icon name="info-circle" size="md"></Icon>
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
                  showError={!isFormValid}
                />
              </VerticalGroup>
            </div>
          </div>
          <div className={cx('footer')}>
            <HorizontalGroup justify="space-between">
              <Text type="secondary">Timezone: {getTzOffsetString(dayjs().tz(currentTimezone))}</Text>
              <HorizontalGroup>
                <Button variant="secondary" onClick={onHide}>
                  {shiftId === 'new' ? 'Cancel' : 'Close'}
                </Button>
                <Button variant="primary" onClick={handleCreate} disabled={!isFormValid || disableAction}>
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
  hideWeekday: boolean;
  shiftStart: dayjs.Dayjs;
  shiftEnd: dayjs.Dayjs;
  setShiftStart: (moment: dayjs.Dayjs) => void;
  setShiftEnd: (moment: dayjs.Dayjs) => void;
  currentTimezone: Timezone;
}

const ShiftPeriod = ({
  hideWeekday,
  shiftStart,
  shiftEnd,
  setShiftStart,
  setShiftEnd,
  currentTimezone,
}: ShiftPeriodProps) => {
  const handleShiftStartWeekdayChange = useCallback(
    (value) => {
      const newShiftStart = shiftStart.add(value, 'day');

      setShiftStart(newShiftStart);
    },
    [shiftStart]
  );

  const handleShiftStartTimeChange = useCallback(
    (h, m, s) => {
      const newShiftStart = shiftStart.tz(currentTimezone).set('hour', h).set('minute', m).set('second', s);

      setShiftStart(newShiftStart);
    },
    [shiftStart]
  );

  const handleShiftEndWeekdayChange = useCallback(
    (value) => {
      const newShiftEnd = shiftEnd.add(value, 'day');

      setShiftEnd(newShiftEnd);
    },
    [shiftEnd]
  );

  const handleShiftEndTimeChange = useCallback(
    (h, m, s) => {
      const newShiftEnd = shiftEnd.tz(currentTimezone).set('hour', h).set('minute', m).set('second', s);

      setShiftEnd(newShiftEnd);
    },
    [shiftEnd]
  );

  return (
    <div className={cx(hideWeekday ? 'three-fields' : 'two-fields')}>
      <Field
        className={cx('date-time-picker')}
        label={
          <Text type="primary" size="small">
            From
          </Text>
        }
      >
        <WeekdayTimePicker
          hideWeekday={hideWeekday}
          value={shiftStart}
          onWeekDayChange={handleShiftStartWeekdayChange}
          onTimeChange={handleShiftStartTimeChange}
          timezone={currentTimezone}
          weekStart={config.bootData.user.weekStart}
        />
      </Field>
      <Field
        className={cx('date-time-picker')}
        label={
          <Text type="primary" size="small">
            Till
          </Text>
        }
      >
        {
          <WeekdayTimePicker
            hideWeekday={hideWeekday}
            value={shiftEnd}
            onWeekDayChange={handleShiftEndWeekdayChange}
            onTimeChange={handleShiftEndTimeChange}
            timezone={currentTimezone}
            weekStart={config.bootData.user.weekStart}
          />
        }
      </Field>
      {hideWeekday && <Text type="secondary">({toHHmmss(shiftEnd.diff(shiftStart, 'second'))})</Text>}
    </div>
  );
};

export default RotationForm2;
