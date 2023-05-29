import React, { FC, useCallback, useEffect, useMemo, useState } from 'react';

import { config } from '@grafana/runtime';
import { IconButton, VerticalGroup, HorizontalGroup, Field, Button, Select, InlineSwitch } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';
import Draggable from 'react-draggable';

import Modal from 'components/Modal/Modal';
import Text from 'components/Text/Text';
import UserGroups from 'components/UserGroups/UserGroups';
import RemoteSelect from 'containers/RemoteSelect/RemoteSelect';
import { getFromString } from 'models/schedule/schedule.helpers';
import { Schedule, Shift } from 'models/schedule/schedule.types';
import { getTzOffsetString } from 'models/timezone/timezone.helpers';
import { Timezone } from 'models/timezone/timezone.types';
import { User } from 'models/user/user.types';
import { getDateTime, getStartOfWeek, getUTCByDay, getUTCString } from 'pages/schedule/Schedule.helpers';
import { useStore } from 'state/useStore';
import { getCoords, waitForElement } from 'utils/DOM';
import { GRAFANA_HEADER_HEIGTH } from 'utils/consts';
import { useDebouncedCallback } from 'utils/hooks';

import DateTimePicker from './parts/DateTimePicker';
import DaysSelector from './parts/DaysSelector';
import DeletionModal from './parts/DeletionModal';
import UserItem from './parts/UserItem';

import styles from './RotationForm.module.css';

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
}

const cx = cn.bind(styles);

const repeatShiftsEveryOptions = Array.from(Array(31).keys())
  .slice(1)
  .map((i) => ({ label: String(i), value: i }));

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
    shiftStart: propsShiftStart = getStartOfWeek(currentTimezone),
    shiftEnd: propsShiftEnd,
    shiftColor = '#3D71D9',
  } = props;

  const [rotationTitle, setRotationTitle] = useState<string>(`[L${layerPriority}] Rotation`);
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [offsetTop, setOffsetTop] = useState<number>(0);
  const [repeatEveryValue, setRepeatEveryValue] = useState<number>(1);
  const [repeatEveryPeriod, setRepeatEveryPeriod] = useState<number>(0);
  const [selectedDays, setSelectedDays] = useState<string[]>([]);
  const [shiftStart, setShiftStart] = useState<dayjs.Dayjs>(propsShiftStart);
  const [shiftEnd, setShiftEnd] = useState<dayjs.Dayjs>(propsShiftEnd || shiftStart.add(1, 'day'));
  const [rotationStart, setRotationStart] = useState<dayjs.Dayjs>(shiftStart);
  const [endLess, setEndless] = useState<boolean>(true);
  const [rotationEnd, setRotationEnd] = useState<dayjs.Dayjs>(shiftStart.add(1, 'month'));
  const [showDeleteRotationConfirmation, setShowDeleteRotationConfirmation] = useState<boolean>(false);

  const store = useStore();
  const shift = store.scheduleStore.shifts[shiftId];

  useEffect(() => {
    if (rotationStart.isBefore(shiftStart)) {
      setRotationStart(shiftStart);
    }
  }, [rotationStart, shiftStart]);

  const updateShiftStart = useCallback(
    (value) => {
      const diff = shiftEnd.diff(shiftStart);

      setShiftStart(value);
      setShiftEnd(value.add(diff));
    },
    [shiftStart, shiftEnd]
  );

  useEffect(() => {
    if (isOpen) {
      waitForElement(`#layer${shiftId === 'new' ? layerPriority : shift?.priority_level}`).then((elm) => {
        const modal = document.querySelector(`.${cx('draggable')}`) as HTMLDivElement;
        const coords = getCoords(elm);

        const offsetTop = Math.min(
          Math.max(coords.top - modal?.offsetHeight - 10, GRAFANA_HEADER_HEIGTH + 10),
          document.body.offsetHeight - modal?.offsetHeight - 10
        );

        setOffsetTop(offsetTop);
      });
    }
  }, [isOpen]);

  const [userGroups, setUserGroups] = useState([]);

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

  useEffect(handleChange, [params]);

  useEffect(() => {
    if (shift) {
      setRotationTitle(shift.title || `[L${shift.priority_level}] Rotation`);
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

  const handleRotationTitleChange = useCallback(
    (title: string) => {
      setRotationTitle(title);
      if (shiftId !== 'new') {
        store.scheduleStore.updateRotation(shiftId, { ...params, title }).catch((error) => {
          if (error.response?.data?.title) {
            setRotationTitle(shift.title || `[L${shift.priority_level}] Rotation`);
          }
        });
      }
    },
    [shiftId, params, shift]
  );

  const handleChangeEndless = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      setEndless(!event.currentTarget.checked);
    },
    [endLess]
  );

  const handleRepeatEveryValueChange = useCallback((option) => {
    setRepeatEveryValue(option.value);
  }, []);

  const isFormValid = useMemo(() => userGroups.some((group) => group.length), [userGroups]);
  const disableAction = !endLess && rotationEnd.isBefore(dayjs().tz(currentTimezone));

  const [focusElementName, setFocusElementName] = useState<undefined | string>(undefined);

  const getFocusHandler = (elementName: string) => {
    return () => {
      setFocusElementName(elementName);
    };
  };

  const handleBlur = useCallback(() => {
    setFocusElementName(undefined);
  }, []);

  useEffect(() => {
    store.scheduleStore.setRotationFormLiveParams({
      rotationStart,
      shiftStart,
      shiftEnd,
      focusElementName,
    });
  }, [params, focusElementName]);

  return (
    <>
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
        <>
          <div className={cx('title')}>
            <HorizontalGroup justify="space-between">
              <Text.Title onTextChange={handleRotationTitleChange} level={5} editable>
                {rotationTitle}
              </Text.Title>
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
          <VerticalGroup>
            <div className={cx('content')}>
              <VerticalGroup>
                <div className={cx('two-fields')}>
                  <Field
                    label={
                      <Text type="primary" size="small">
                        Rotation start
                      </Text>
                    }
                  >
                    <DateTimePicker
                      minMoment={shiftStart}
                      value={rotationStart}
                      onChange={setRotationStart}
                      timezone={currentTimezone}
                      onFocus={getFocusHandler('rotationStart')}
                      onBlur={handleBlur}
                    />
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
                      <div style={{ lineHeight: '32px' }}>
                        <Text type="secondary">Endless</Text>
                      </div>
                    ) : (
                      <DateTimePicker value={rotationEnd} onChange={setRotationEnd} timezone={currentTimezone} />
                    )}
                  </Field>
                </div>
                <HorizontalGroup>
                  <Field className={cx('control')} label="Repeat shifts every">
                    <Select
                      maxMenuHeight={120}
                      value={repeatEveryValue}
                      options={repeatShiftsEveryOptions}
                      onChange={handleRepeatEveryValueChange}
                      allowCustomValue
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
                <Field label="Select days to repeat">
                  <DaysSelector
                    weekStart={config.bootData.user.weekStart}
                    options={store.scheduleStore.byDayOptions}
                    value={selectedDays}
                    onChange={(value) => setSelectedDays(value)}
                  />
                </Field>
                <div className={cx('two-fields')}>
                  <Field
                    className={cx('date-time-picker')}
                    label={
                      <Text type="primary" size="small">
                        Parent shift start
                      </Text>
                    }
                  >
                    <DateTimePicker
                      value={shiftStart}
                      onChange={updateShiftStart}
                      timezone={currentTimezone}
                      onFocus={getFocusHandler('shiftStart')}
                      onBlur={handleBlur}
                    />
                  </Field>
                  <Field
                    className={cx('date-time-picker')}
                    label={
                      <Text type="primary" size="small">
                        Parent shift end
                      </Text>
                    }
                  >
                    <DateTimePicker
                      value={shiftEnd}
                      onChange={setShiftEnd}
                      timezone={currentTimezone}
                      onFocus={getFocusHandler('shiftEnd')}
                      onBlur={handleBlur}
                    />
                  </Field>
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
          </VerticalGroup>
        </>
      </Modal>
      {showDeleteRotationConfirmation && (
        <DeletionModal onHide={() => setShowDeleteRotationConfirmation(false)} onConfirm={handleDeleteClick} />
      )}
    </>
  );
});

export default RotationForm;
