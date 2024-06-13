import React, { FC, useCallback, useEffect, useMemo, useState } from 'react';

import { IconButton, VerticalGroup, HorizontalGroup, Field, Button, useTheme2 } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import Draggable from 'react-draggable';

import { Modal } from 'components/Modal/Modal';
import { Tag } from 'components/Tag/Tag';
import { Text } from 'components/Text/Text';
import { UserGroups } from 'components/UserGroups/UserGroups';
import { WithConfirm } from 'components/WithConfirm/WithConfirm';
import { getShiftName } from 'models/schedule/schedule.helpers';
import { Schedule, Shift } from 'models/schedule/schedule.types';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { getDateTime, getUTCString } from 'pages/schedule/Schedule.helpers';
import { useStore } from 'state/useStore';
import { HTML_ID, getCoords, waitForElement } from 'utils/DOM';
import { GRAFANA_HEADER_HEIGHT } from 'utils/consts';
import { useDebouncedCallback } from 'utils/hooks';

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
  const {
    onHide,
    onCreate,
    scheduleId,
    onUpdate,
    onDelete,
    shiftId,
    shiftStart: propsShiftStart = dayjs().startOf('day').add(1, 'day'),
    shiftEnd: propsShiftEnd,
    shiftColor: shiftColorProp,
  } = props;

  const store = useStore();
  const theme = useTheme2();

  const [rotationName, setRotationName] = useState<string>(shiftId === 'new' ? 'Override' : 'Update override');

  const [shiftStart, setShiftStart] = useState<dayjs.Dayjs>(propsShiftStart);
  const [shiftEnd, setShiftEnd] = useState<dayjs.Dayjs>(propsShiftEnd || propsShiftStart.add(24, 'hours'));

  const [offsetTop, setOffsetTop] = useState<number>(0);

  const [isOpen, setIsOpen] = useState<boolean>(false);

  const [errors, setErrors] = useState<{ [key: string]: string[] }>({});
  const shiftColor = shiftColorProp || theme.colors.warning.main;

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
        const elm = await waitForElement(`#${HTML_ID.SCHEDULE_OVERRIDES_AND_SWAPS}`);
        const modal = document.querySelector(`.${cx('draggable')}`) as HTMLDivElement;
        const coords = getCoords(elm);
        const offsetTop = Math.min(
          Math.max(coords.top - modal?.offsetHeight - 10, GRAFANA_HEADER_HEIGHT + 10),
          document.body.offsetHeight - modal?.offsetHeight - 10
        );

        setOffsetTop(offsetTop);
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
        <Draggable handle=".drag-handler" defaultClassName={cx('draggable')} positionOffset={{ x: 0, y: offsetTop }}>
          <div {...props}>{children}</div>
        </Draggable>
      )}
    >
      <VerticalGroup>
        <HorizontalGroup justify="space-between">
          <HorizontalGroup spacing="sm">
            {shiftId === 'new' && <Tag color={shiftColor}>New</Tag>}
            <Text.Title onTextChange={handleRotationNameChange} level={5} editable>
              {rotationName}
            </Text.Title>
          </HorizontalGroup>
          <HorizontalGroup>
            {shiftId !== 'new' && (
              <WithConfirm>
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
          </HorizontalGroup>
        </HorizontalGroup>
        <div className={cx('override-form-content')} data-testid="override-inputs">
          <VerticalGroup>
            <HorizontalGroup align="flex-start">
              <Field
                className={cx('date-time-picker')}
                label={
                  <Text type="primary" size="small">
                    Override period start
                  </Text>
                }
              >
                <DateTimePicker
                  disabled={disabled}
                  value={shiftStart}
                  onChange={updateShiftStart}
                  error={errors.shift_start}
                />
              </Field>
              <Field
                className={cx('date-time-picker')}
                label={
                  <Text type="primary" size="small">
                    Override period end
                  </Text>
                }
              >
                <DateTimePicker disabled={disabled} value={shiftEnd} onChange={setShiftEnd} error={errors.shift_end} />
              </Field>
            </HorizontalGroup>
            <UserGroups
              disabled={disabled}
              value={userGroups}
              onChange={setUserGroups}
              isMultipleGroups={false}
              renderUser={(pk: ApiSchemas['User']['pk']) => (
                <UserItem pk={pk} shiftColor={shiftColor} shiftStart={params.shift_start} shiftEnd={params.shift_end} />
              )}
              showError={Boolean(errors.rolling_users)}
            />
          </VerticalGroup>
        </div>
        <HorizontalGroup justify="space-between">
          <Text type="secondary">Current timezone: {store.timezoneStore.selectedTimezoneLabel}</Text>
          <HorizontalGroup>
            <Button variant="primary" onClick={handleCreate} disabled={disabled || !isFormValid}>
              {shiftId === 'new' ? 'Create' : 'Update'}
            </Button>
          </HorizontalGroup>
        </HorizontalGroup>
      </VerticalGroup>
    </Modal>
  );
};
