import React, { FC, useCallback, useEffect, useMemo, useState } from 'react';

import { IconButton, Stack, Field, Button, useTheme2 } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import Draggable, { DraggableData, DraggableEvent } from 'react-draggable';

import { Modal } from 'components/Modal/Modal';
import { Tag } from 'components/Tag/Tag';
import { Text } from 'components/Text/Text';
import { UserGroups } from 'components/UserGroups/UserGroups';
import { WithConfirm } from 'components/WithConfirm/WithConfirm';
import { calculateScheduleFormOffset } from 'containers/Rotations/Rotations.helpers';
import { getShiftName } from 'models/schedule/schedule.helpers';
import { Schedule, Shift } from 'models/schedule/schedule.types';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { getDateTime, getUTCString, toDateWithTimezoneOffset } from 'pages/schedule/Schedule.helpers';
import { useStore } from 'state/useStore';
import { StackSize } from 'utils/consts';
import { useDebouncedCallback, useResize } from 'utils/hooks';

import { getDraggableModalCoordinatesOnInit } from './RotationForm.helpers';
import { DateTimePicker } from './parts/DateTimePicker';
import { UserItem } from './parts/UserItem';

import styles from './RotationForm.module.css';

interface RotationFormProps {
  onHide: () => void;
  shiftId: Shift['id'] | 'new';
  scheduleId: Schedule['id'];
  shiftStart?: dayjs.Dayjs;
  shiftEnd?: dayjs.Dayjs;
  shiftColor?: string;
  onCreate: () => void;
  onUpdate: () => void;
  onDelete: () => void;
}

const cx = cn.bind(styles);

export const ScheduleOverrideForm: FC<RotationFormProps> = (props) => {
  const store = useStore();
  const theme = useTheme2();

  const {
    onHide,
    onCreate,
    scheduleId,
    onUpdate,
    onDelete,
    shiftId,
    shiftStart: propsShiftStart = store.timezoneStore.calendarStartDate,
    shiftEnd: propsShiftEnd,
    shiftColor: shiftColorProp,
  } = props;

  const [rotationName, setRotationName] = useState<string>(shiftId === 'new' ? 'Override' : 'Update override');

  const [draggablePosition, setDraggablePosition] = useState<{ x: number; y: number }>(undefined);
  const [bounds, setDraggableBounds] = useState<{ left: number; right: number; top: number; bottom: number }>(
    undefined
  );

  const [shiftStart, setShiftStart] = useState<dayjs.Dayjs>(propsShiftStart);
  const [shiftEnd, setShiftEnd] = useState<dayjs.Dayjs>(propsShiftEnd || propsShiftStart.add(24, 'hours'));

  const [offsetTop, setOffsetTop] = useState<number>(0);

  const [isOpen, setIsOpen] = useState<boolean>(false);

  const [errors, setErrors] = useState<{ [key: string]: string[] }>({});
  const shiftColor = shiftColorProp || theme.colors.warning.main;

  const debouncedOnResize = useDebouncedCallback(onResize, 250);

  useResize(debouncedOnResize);

  const updateShiftStart = useCallback(
    (value) => {
      const diff = shiftEnd.diff(shiftStart);

      setShiftStart(value);
      setShiftEnd(value.add(diff));
    },
    [shiftStart, shiftEnd]
  );

  useEffect(() => {
    (async () => {
      if (isOpen) {
        setOffsetTop(await calculateScheduleFormOffset(`.${cx('draggable')}`));
      }
    })();
  }, [isOpen]);

  const [userGroups, setUserGroups] = useState([[]]);

  const shift = store.scheduleStore.shifts[shiftId];

  useEffect(() => {
    if (shiftId !== 'new') {
      store.scheduleStore.updateOncallShift(shiftId);
    }
  }, [shiftId]);

  useEffect(() => {
    setShiftStart(toDateWithTimezoneOffset(shiftStart, store.timezoneStore.selectedTimezoneOffset));
    setShiftEnd(toDateWithTimezoneOffset(shiftEnd, store.timezoneStore.selectedTimezoneOffset));
  }, [store.timezoneStore.selectedTimezoneOffset]);

  const params = useMemo(
    () => ({
      rotation_start: getUTCString(shiftStart),
      shift_start: getUTCString(shiftStart),
      shift_end: getUTCString(shiftEnd),
      rolling_users: userGroups,
      frequency: null,
      name: rotationName,
    }),
    [shiftStart, shiftEnd, userGroups, rotationName, store.timezoneStore.selectedTimezoneOffset]
  );

  useEffect(() => {
    if (shift) {
      setRotationName(getShiftName(shift));
      setShiftStart(getDateTime(shift.shift_start));
      setShiftEnd(getDateTime(shift.shift_end));

      setUserGroups(shift.rolling_users);
    }
  }, [shift]);

  const handleRotationNameChange = useCallback(
    (name: string) => {
      setRotationName(name);
    },
    [shiftId, params, shift]
  );

  const handleDeleteClick = useCallback(async () => {
    await store.scheduleStore.deleteOncallShift(shiftId);
    onHide();
    onDelete();
  }, []);

  const handleCreate = useCallback(async () => {
    try {
      if (shiftId === 'new') {
        await store.scheduleStore.createRotation(scheduleId, true, params);
        onCreate();
      } else {
        await store.scheduleStore.updateRotation(shiftId, params);
        onUpdate();
      }
    } catch (err) {
      onError(err);
    }
  }, [scheduleId, shiftId, params]);

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
        true,
        params
      );
    } catch (err) {
      onError(err);
    } finally {
      // wait until a scroll to the "Overrides and swaps" happened
      setTimeout(() => {
        setIsOpen(true);
      }, 100);
    }
  };

  const onError = useCallback((error) => {
    if (error.response) {
      setErrors(error.response.data);
    }
  }, []);

  const handleChange = useDebouncedCallback(updatePreview, 200);

  useEffect(handleChange, [params, store.timezoneStore.calendarStartDate, store.timezoneStore.selectedTimezoneOffset]);

  const isFormValid = useMemo(() => !Object.keys(errors).length, [errors]);

  const ended = shift && shift.until && getDateTime(shift.until).isBefore(dayjs());
  const disabled = ended;

  return (
    <Modal
      top="0"
      isOpen={isOpen}
      width="430px"
      onDismiss={onHide}
      contentElement={(props, children) => (
        <Draggable
          handle=".drag-handler"
          defaultClassName={cx('draggable')}
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
      <Stack direction="column">
        <Stack justifyContent="space-between">
          <Stack gap={StackSize.sm}>
            {shiftId === 'new' && <Tag color={shiftColor}>New</Tag>}
            <Text.Title onTextChange={handleRotationNameChange} level={5} editable>
              {rotationName}
            </Text.Title>
          </Stack>
          <Stack>
            {shiftId !== 'new' && (
              <WithConfirm title="Are you sure you want to delete override?">
                <IconButton variant="secondary" tooltip="Delete" name="trash-alt" onClick={handleDeleteClick} />
              </WithConfirm>
            )}
            <IconButton aria-label="Drag" variant="secondary" className={cx('drag-handler')} name="draggabledots" />
            <IconButton
              name="times"
              variant="secondary"
              tooltip={shiftId === 'new' ? 'Cancel' : 'Close'}
              onClick={onHide}
            />
          </Stack>
        </Stack>

        <div className={cx('container')}>
          <div className={cx('override-form-content')} data-testid="override-inputs">
            <Stack direction="column">
              <Stack alignItems="flex-start">
                <Field
                  className={cx('date-time-picker')}
                  data-testid="override-start"
                  label={
                    <Text type="primary" size="small">
                      Override period start
                    </Text>
                  }
                >
                  <DateTimePicker
                    disabled={disabled}
                    value={shiftStart}
                    utcOffset={store.timezoneStore.selectedTimezoneOffset}
                    onChange={updateShiftStart}
                    error={errors.shift_start}
                  />
                </Field>

                <Field
                  className={cx('date-time-picker')}
                  data-testid="override-end"
                  label={
                    <Text type="primary" size="small">
                      Override period end
                    </Text>
                  }
                >
                  <DateTimePicker
                    disabled={disabled}
                    value={shiftEnd}
                    utcOffset={store.timezoneStore.selectedTimezoneOffset}
                    onChange={setShiftEnd}
                    error={errors.shift_end}
                  />
                </Field>
              </Stack>

              <UserGroups
                disabled={disabled}
                value={userGroups}
                onChange={setUserGroups}
                isMultipleGroups={false}
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
        <Stack justifyContent="space-between">
          <Text type="secondary">
            Current timezone: <Text type="primary">{store.timezoneStore.selectedTimezoneLabel}</Text>
          </Text>
          <Stack>
            <Button variant="primary" onClick={handleCreate} disabled={disabled || !isFormValid}>
              {shiftId === 'new' ? 'Create' : 'Update'}
            </Button>
          </Stack>
        </Stack>
      </Stack>
    </Modal>
  );

  async function onResize() {
    setOffsetTop(await calculateScheduleFormOffset(`.${cx('draggable')}`));

    setDraggablePosition({ x: 0, y: 0 });
  }

  function onDraggableInit(_e: DraggableEvent, data: DraggableData) {
    if (!data) {
      return;
    }

    setDraggableBounds(getDraggableModalCoordinatesOnInit(data, offsetTop));
  }
};
