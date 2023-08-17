import React, { FC, useCallback, useEffect, useMemo, useState } from 'react';

import { IconButton, VerticalGroup, HorizontalGroup, Field, Button } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import Draggable from 'react-draggable';

import Modal from 'components/Modal/Modal';
import Tag from 'components/Tag/Tag';
import Text from 'components/Text/Text';
import UserGroups from 'components/UserGroups/UserGroups';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import { getShiftName } from 'models/schedule/schedule.helpers';
import { Schedule, Shift } from 'models/schedule/schedule.types';
import { getTzOffsetString } from 'models/timezone/timezone.helpers';
import { Timezone } from 'models/timezone/timezone.types';
import { User } from 'models/user/user.types';
import { getDateTime, getUTCString } from 'pages/schedule/Schedule.helpers';
import { useStore } from 'state/useStore';
import { getCoords, getVar, waitForElement } from 'utils/DOM';
import { GRAFANA_HEADER_HEIGHT } from 'utils/consts';
import { useDebouncedCallback } from 'utils/hooks';

import DateTimePicker from './parts/DateTimePicker';
import UserItem from './parts/UserItem';

import styles from './RotationForm.module.css';

interface RotationFormProps {
  onHide: () => void;
  shiftId: Shift['id'] | 'new';
  startMoment: dayjs.Dayjs;
  currentTimezone: Timezone;
  scheduleId: Schedule['id'];
  shiftStart?: dayjs.Dayjs;
  shiftEnd?: dayjs.Dayjs;
  shiftColor?: string;
  onCreate: () => void;
  onUpdate: () => void;
  onDelete: () => void;
}

const cx = cn.bind(styles);

const ScheduleOverrideForm: FC<RotationFormProps> = (props) => {
  const {
    onHide,
    onCreate,
    currentTimezone,
    scheduleId,
    onUpdate,
    onDelete,
    shiftId,
    startMoment,
    shiftStart: propsShiftStart = dayjs().startOf('day').add(1, 'day'),
    shiftEnd: propsShiftEnd,
    shiftColor = getVar('--tag-warning'),
  } = props;

  const store = useStore();

  const [rotationName, setRotationName] = useState<string>(shiftId === 'new' ? 'Override' : 'Update override');

  const [shiftStart, setShiftStart] = useState<dayjs.Dayjs>(propsShiftStart);
  const [shiftEnd, setShiftEnd] = useState<dayjs.Dayjs>(propsShiftEnd || propsShiftStart.add(24, 'hours'));

  const [offsetTop, setOffsetTop] = useState<number>(0);

  const [isOpen, setIsOpen] = useState<boolean>(false);

  const [errors, setErrors] = useState<{ [key: string]: string[] }>({});

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
      waitForElement('#overrides-list').then((elm) => {
        const modal = document.querySelector(`.${cx('draggable')}`) as HTMLDivElement;

        const coords = getCoords(elm);

        const offsetTop = Math.min(
          Math.max(coords.top - modal?.offsetHeight - 10, GRAFANA_HEADER_HEIGHT + 10),
          document.body.offsetHeight - modal?.offsetHeight - 10
        );

        setOffsetTop(offsetTop);
      });
    }
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
    [currentTimezone, shiftStart, shiftEnd, userGroups, rotationName]
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

  const handleDeleteClick = useCallback(() => {
    store.scheduleStore.deleteOncallShift(shiftId).then(() => {
      onHide();

      onDelete();
    });
  }, []);

  const handleCreate = useCallback(() => {
    if (shiftId === 'new') {
      store.scheduleStore
        .createRotation(scheduleId, true, params)
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

  useEffect(() => {
    if (shiftId === 'new') {
      updatePreview();
    }
  }, []);

  const updatePreview = () => {
    setErrors({});

    store.scheduleStore
      .updateRotationPreview(scheduleId, shiftId, startMoment, true, params)
      .catch(onError)
      .finally(() => {
        setIsOpen(true);
      });
  };

  const onError = useCallback((error) => {
    setErrors(error.response.data);
  }, []);

  const handleChange = useDebouncedCallback(updatePreview, 200);

  useEffect(handleChange, [params, startMoment]);

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
            <IconButton variant="secondary" className={cx('drag-handler')} name="draggabledots" />
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
                  timezone={currentTimezone}
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
                <DateTimePicker
                  disabled={disabled}
                  value={shiftEnd}
                  onChange={setShiftEnd}
                  timezone={currentTimezone}
                  error={errors.shift_end}
                />
              </Field>
            </HorizontalGroup>
            <UserGroups
              disabled={disabled}
              value={userGroups}
              onChange={setUserGroups}
              isMultipleGroups={false}
              renderUser={(pk: User['pk']) => (
                <UserItem pk={pk} shiftColor={shiftColor} shiftStart={params.shift_start} shiftEnd={params.shift_end} />
              )}
              showError={Boolean(errors.rolling_users)}
            />
          </VerticalGroup>
        </div>
        <HorizontalGroup justify="space-between">
          <Text type="secondary">Current timezone: {getTzOffsetString(dayjs().tz(currentTimezone))}</Text>
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

export default ScheduleOverrideForm;
