import React, { FC, useCallback, useEffect, useMemo, useState } from 'react';

import { dateTime, DateTime } from '@grafana/data';
import {
  IconButton,
  VerticalGroup,
  HorizontalGroup,
  Field,
  Input,
  Button,
  DateTimePicker,
  Select,
  InlineSwitch,
} from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';
import Draggable from 'react-draggable';

import Modal from 'components/Modal/Modal';
import ScheduleSlot from 'components/ScheduleSlot/ScheduleSlot';
import Text from 'components/Text/Text';
import UserGroups from 'components/UserGroups/UserGroups';
import { Item } from 'components/UserGroups/UserGroups.types';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import WorkingHours from 'components/WorkingHours/WorkingHours';
import RemoteSelect from 'containers/RemoteSelect/RemoteSelect';
import { getFromString } from 'models/schedule/schedule.helpers';
import { Rotation, Schedule, Shift } from 'models/schedule/schedule.types';
import { getTzOffsetString } from 'models/timezone/timezone.helpers';
import { Timezone } from 'models/timezone/timezone.types';
import { User } from 'models/user/user.types';
import { makeRequest } from 'network';
import { getDateTime, getUTCString } from 'pages/schedule/Schedule.helpers';
import { SelectOption } from 'state/types';
import { useStore } from 'state/useStore';
import { getCoords, waitForElement } from 'utils/DOM';
import { useDebouncedCallback } from 'utils/hooks';

import { RotationCreateData } from './RotationForm.types';

import styles from './RotationForm.module.css';

interface RotationFormProps {
  layerPriority: number;
  onHide: () => void;
  startMoment: dayjs.Dayjs;
  currentTimezone: Timezone;
  scheduleId: Schedule['id'];
  shiftId: Shift['id'] | 'new';
  shiftMoment?: dayjs.Dayjs;
  onCreate: () => void;
  onUpdate: () => void;
  onDelete: () => void;
  shiftColor?: string;
}

const cx = cn.bind(styles);

const RotationForm: FC<RotationFormProps> = observer((props) => {
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
    shiftMoment = dayjs().startOf('isoWeek'),
    shiftColor = '#3D71D9',
  } = props;

  // console.log('shiftColor', shiftColor);

  const [isOpen, setIsOpen] = useState<boolean>(false);

  const [repeatEveryValue, setRepeatEveryValue] = useState<number>(1);
  const [repeatEveryPeriod, setRepeatEveryPeriod] = useState<number>(0);
  const [selectedDays, setSelectedDays] = useState<string[]>([]);
  const [shiftStart, setShiftStart] = useState<DateTime>(dateTime(shiftMoment.format('YYYY-MM-DD HH:mm:ss')));
  const [shiftEnd, setShiftEnd] = useState<DateTime>(dateTime(shiftMoment.add(1, 'day').format('YYYY-MM-DD HH:mm:ss')));
  const [rotationStart, setRotationStart] = useState<DateTime>(dateTime(shiftMoment.format('YYYY-MM-DD HH:mm:ss')));
  const [endLess, setEndless] = useState<boolean>(true);
  const [rotationEnd, setRotationEnd] = useState<DateTime>(
    dateTime(shiftMoment.add(1, 'month').format('YYYY-MM-DD HH:mm:ss'))
  );

  const store = useStore();

  const shift = store.scheduleStore.shifts[shiftId];

  const [offsetTop, setOffsetTop] = useState<number>(0);

  useEffect(() => {
    if (isOpen) {
      waitForElement(`#layer${shiftId === 'new' ? layerPriority : shift?.priority_level}`).then((elm) => {
        const modal = document.querySelector(`.${cx('draggable')}`) as HTMLDivElement;

        const coords = getCoords(elm);

        // elm.scrollIntoView({ behavior: 'smooth', block: 'end', inline: 'nearest' });
        // setOffsetTop(Math.max(coords.top + elm.offsetHeight, 0));

        setOffsetTop(Math.max(coords.top - modal?.offsetHeight - 10, 10));
      });
    }
  }, [isOpen]);

  const [userGroups, setUserGroups] = useState(shiftId === 'new' ? [[store.userStore.currentUserPk]] : [[]]);

  const getUser = (pk: User['pk']) => {
    return {
      name: store.userStore.items[pk]?.username,
      desc: store.userStore.items[pk]?.timezone,
    };
  };

  const renderUser = (userPk: User['pk']) => {
    const name = store.userStore.items[userPk]?.username;
    const desc = store.userStore.items[userPk]?.timezone;
    const workingHours = store.userStore.items[userPk]?.working_hours;
    const timezone = store.userStore.items[userPk]?.timezone;

    return (
      <>
        <div className={cx('user-title')}>
          <Text strong>{name}</Text> <Text type="primary">({desc})</Text>
        </div>
        <WorkingHours
          timezone={timezone}
          workingHours={workingHours}
          startMoment={dayjs(params.shift_start)}
          duration={dayjs(params.shift_end).diff(dayjs(params.shift_start), 'seconds')}
          className={cx('working-hours')}
          style={{ backgroundColor: shiftColor }}
        />
      </>
    );
  };

  const handleDeleteClick = useCallback(() => {
    store.scheduleStore.deleteOncallShift(shiftId).then(() => {
      onDelete();
    });
  }, []);

  useEffect(() => {
    if (shiftId !== 'new') {
      store.scheduleStore.updateOncallShift(shiftId);
    }
  }, [shiftId]);

  const params = useMemo(
    () => ({
      rotation_start: getUTCString(rotationStart, currentTimezone),
      until: endLess ? null : getUTCString(rotationEnd, currentTimezone),
      shift_start: getUTCString(shiftStart, currentTimezone),
      shift_end: getUTCString(shiftEnd, currentTimezone),
      rolling_users: userGroups,
      interval: repeatEveryValue,
      frequency: repeatEveryPeriod,
      by_day: repeatEveryPeriod === 1 ? selectedDays : null,
      priority_level: shiftId === 'new' ? layerPriority : shift?.priority_level,
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
    ]
  );

  const handleCreate = useCallback(() => {
    if (shiftId === 'new') {
      store.scheduleStore.createRotation(scheduleId, false, params).then(() => {
        onCreate();
      });
    } else {
      store.scheduleStore.updateRotation(shiftId, params).then(() => {
        onUpdate();
      });
    }
  }, [scheduleId, shiftId, params]);

  useEffect(() => {
    if (shiftId === 'new') {
      updatePreview();
    }
  }, []);

  const updatePreview = () => {
    store.scheduleStore
      .updateRotationPreview(scheduleId, shiftId, getFromString(startMoment), false, params)
      .then(() => {
        setIsOpen(true);
      });
  };

  const handleChange = useDebouncedCallback(updatePreview, 200);

  useEffect(handleChange, [params]);

  useEffect(() => {
    if (shift) {
      setRotationStart(getDateTime(shift.rotation_start));
      setRotationEnd(getDateTime(shift.until));
      setShiftStart(getDateTime(shift.shift_start));
      setShiftEnd(getDateTime(shift.shift_end));
      setEndless(!shift.until);

      setRepeatEveryValue(shift.interval);
      setRepeatEveryPeriod(shift.frequency);
      setSelectedDays(shift.by_day);

      setUserGroups(shift.rolling_users);
    }
  }, [shift]);

  const handleChangeEndless = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      setEndless(!event.currentTarget.checked);
    },
    [endLess]
  );

  const handleRepeatEveryValueChange = useCallback((option) => {
    setRepeatEveryValue(option.value);
  }, []);

  const moment = dayjs();

  return (
    <Modal
      isOpen={isOpen}
      width="430px"
      onDismiss={onHide}
      contentElement={(props, children) => (
        <Draggable handle=".drag-handler" defaultClassName={cx('draggable')} positionOffset={{ x: 0, y: offsetTop }}>
          <div {...props}>{children}</div>
        </Draggable>
      )}
    >
      <VerticalGroup>
        <HorizontalGroup justify="space-between">
          <Text size="medium">
            <HorizontalGroup spacing="sm">
              <span>[L{shiftId === 'new' ? layerPriority : shift?.priority_level}]</span>
              {shiftId === 'new' ? 'New Rotation' : shift?.id}
            </HorizontalGroup>
          </Text>
          <HorizontalGroup>
            <IconButton disabled variant="secondary" tooltip="Copy" name="copy" />
            <IconButton disabled variant="secondary" tooltip="Code" name="brackets-curly" />
            {shiftId !== 'new' && (
              <WithConfirm>
                <IconButton variant="secondary" tooltip="Delete" name="trash-alt" onClick={handleDeleteClick} />
              </WithConfirm>
            )}
            <IconButton variant="secondary" className={cx('drag-handler')} name="draggabledots" />
          </HorizontalGroup>
        </HorizontalGroup>
        <UserGroups
          value={userGroups}
          onChange={setUserGroups}
          isMultipleGroups={true}
          getItemData={getUser}
          renderUser={renderUser}
        />
        {/*<hr />*/}
        <VerticalGroup>
          <HorizontalGroup>
            <Field className={cx('control')} label="Repeat shifts every">
              <Select
                value={repeatEveryValue}
                options={[
                  { label: '1', value: 1 },
                  { label: '2', value: 2 },
                  { label: '3', value: 3 },
                  { label: '4', value: 4 },
                  { label: '5', value: 5 },
                  { label: '6', value: 6 },
                  { label: '7', value: 7 },
                ]}
                onChange={handleRepeatEveryValueChange}
              />
            </Field>
            <Field className={cx('control')} label="">
              <RemoteSelect
                href="/oncall_shifts/frequency_options/"
                value={repeatEveryPeriod}
                onChange={setRepeatEveryPeriod}
              />
            </Field>
          </HorizontalGroup>
          {repeatEveryPeriod === 1 && (
            /*<HorizontalGroup justify="center">*/
            <Field label="Select days to repeat">
              <DaysSelector
                options={store.scheduleStore.byDayOptions}
                value={selectedDays}
                onChange={(value) => setSelectedDays(value)}
              />
            </Field>
            /*</HorizontalGroup>*/
          )}
          <HorizontalGroup>
            <Field
              className={cx('date-time-picker')}
              label={
                <Text type="primary" size="small">
                  Shift start
                </Text>
              }
            >
              <DateTimePicker date={shiftStart} onChange={setShiftStart} />
            </Field>
            <Field
              className={cx('date-time-picker')}
              label={
                <Text type="primary" size="small">
                  Shift end
                </Text>
              }
            >
              <DateTimePicker date={shiftEnd} onChange={setShiftEnd} />
            </Field>
          </HorizontalGroup>
          <HorizontalGroup>
            <Field
              className={cx('date-time-picker')}
              label={
                <Text type="primary" size="small">
                  Rotation start
                </Text>
              }
            >
              <DateTimePicker date={rotationStart} onChange={setRotationStart} />
            </Field>
            <Field
              label={
                <HorizontalGroup spacing="xs">
                  <Text type="primary" size="small">
                    Rotation end
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
                <Input
                  value="endless"
                  onClick={() => {
                    setEndless(false);
                  }}
                />
              ) : (
                <DateTimePicker date={rotationEnd} onChange={setRotationEnd} />
              )}
            </Field>
          </HorizontalGroup>
        </VerticalGroup>
        <HorizontalGroup justify="space-between">
          <Text type="secondary">Timezone: {getTzOffsetString(dayjs().tz(currentTimezone))}</Text>
          <HorizontalGroup>
            <Button variant="secondary">+ Override</Button>
            <Button variant="primary" onClick={handleCreate}>
              {shiftId === 'new' ? 'Create' : 'Update'}
            </Button>
          </HorizontalGroup>
        </HorizontalGroup>
      </VerticalGroup>
    </Modal>
  );
});

interface DaysSelectorProps {
  value: string[];
  onChange: (value: string[]) => void;
  options: SelectOption[];
}

const DaysSelector = ({ value, onChange, options }: DaysSelectorProps) => {
  const getDayClickHandler = (day: string) => {
    return () => {
      const newValue = [...value];
      if (newValue.includes(day)) {
        const index = newValue.indexOf(day);
        newValue.splice(index, 1);
      } else {
        newValue.push(day);
      }
      onChange(newValue);
    };
  };

  return (
    <div className={cx('days')}>
      {options.map(({ display_name, value: itemValue }) => (
        <div
          onClick={getDayClickHandler(itemValue as string)}
          className={cx('day', { day__selected: value.includes(itemValue as string) })}
        >
          {display_name.charAt(0)}
        </div>
      ))}
    </div>
  );
};

export default RotationForm;
