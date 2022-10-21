import React, { FC, useCallback, useEffect, useMemo, useState } from 'react';

import { IconButton, VerticalGroup, HorizontalGroup, Field, Button } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import Draggable from 'react-draggable';

import Modal from 'components/Modal/Modal';
import Text from 'components/Text/Text';
import UserGroups from 'components/UserGroups/UserGroups';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import WorkingHours from 'components/WorkingHours/WorkingHours';
import { getFromString } from 'models/schedule/schedule.helpers';
import { Schedule, Shift } from 'models/schedule/schedule.types';
import { getTzOffsetString } from 'models/timezone/timezone.helpers';
import { Timezone } from 'models/timezone/timezone.types';
import { User } from 'models/user/user.types';
import { getDateTime, getUTCString } from 'pages/schedule/Schedule.helpers';
import { useStore } from 'state/useStore';
import { getCoords, waitForElement } from 'utils/DOM';
import { useDebouncedCallback } from 'utils/hooks';

import DateTimePicker from './DateTimePicker';

import styles from './RotationForm.module.css';

interface RotationFormProps {
  onHide: () => void;
  shiftId: Shift['id'] | 'new';
  startMoment: dayjs.Dayjs;
  currentTimezone: Timezone;
  scheduleId: Schedule['id'];
  shiftMoment: dayjs.Dayjs;
  shiftColor?: string;
  onCreate: () => void;
  onUpdate: () => void;
  onDelete: () => void;
}

const cx = cn.bind(styles);

const ScheduleOverrideForm: FC<RotationFormProps> = ({
  onHide,
  onCreate,
  currentTimezone,
  scheduleId,
  onUpdate,
  onDelete,
  shiftId,
  startMoment,
  shiftMoment = dayjs().startOf('day').add(1, 'day'),
  shiftColor = '#C69B06',
}) => {
  const {
    userStore: { items },
    scheduleStore: {
      shifts,
      updateOncallShift,
      deleteOncallShift,
      createRotation,
      updateRotation,
      updateRotationPreview,
    },
  } = useStore();

  const shift = shifts[shiftId];

  const [offsetTop, setOffsetTop] = useState<number>(0);
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [shiftStart, setShiftStart] = useState<dayjs.Dayjs>(shiftMoment);
  const [shiftEnd, setShiftEnd] = useState<dayjs.Dayjs>(shiftMoment.add(24, 'hours'));
  const [userGroups, setUserGroups] = useState([[]]);

  useEffect(() => {
    if (isOpen) {
      waitForElement('#overrides-list').then((elm) => {
        const modal = document.querySelector(`.${cx('draggable')}`) as HTMLDivElement;

        const coords = getCoords(elm);

        const offsetTop = Math.min(
          Math.max(coords.top - modal?.offsetHeight - 10, 10),
          document.body.offsetHeight - modal?.offsetHeight - 10
        );

        setOffsetTop(offsetTop);
      });
    }
  }, [isOpen]);

  const params = useMemo(
    () => ({
      rotation_start: getUTCString(shiftStart),
      shift_start: getUTCString(shiftStart),
      shift_end: getUTCString(shiftEnd),
      rolling_users: userGroups,
      frequency: null,
    }),
    [shiftStart, shiftEnd, userGroups]
  );

  const { shift_start, shift_end } = params;

  const renderUser = useCallback(
    (userPk: User['pk']) => {
      const name = items[userPk]?.username;
      const desc = items[userPk]?.timezone;
      const workingHours = items[userPk]?.working_hours;
      const timezone = items[userPk]?.timezone;

      return (
        <>
          <div className={cx('user-title')}>
            <Text strong>{name}</Text> <Text style={{ color: 'var(--always-gray)' }}>({desc})</Text>
          </div>
          <WorkingHours
            timezone={timezone}
            workingHours={workingHours}
            startMoment={dayjs(shift_start)}
            duration={dayjs(shift_end).diff(dayjs(shift_start), 'seconds')}
            className={cx('working-hours')}
            style={{ backgroundColor: shiftColor }}
          />
        </>
      );
    },
    [items, shift_start, shift_end, shiftColor]
  );

  const updatePreview = useCallback(() => {
    updateRotationPreview(scheduleId, shiftId, getFromString(startMoment), true, params).then(() => {
      setIsOpen(true);
    });
  }, [updateRotationPreview, scheduleId, shiftId, startMoment, params]);

  useEffect(() => {
    if (shiftId !== 'new') {
      updateOncallShift(shiftId);
      updatePreview();
    }
  }, [shiftId, updateOncallShift, updatePreview]);

  useEffect(() => {
    if (shift) {
      setShiftStart(getDateTime(shift.shift_start));
      setShiftEnd(getDateTime(shift.shift_end));

      setUserGroups(shift.rolling_users);
    }
  }, [shift]);

  const handleDeleteClick = useCallback(() => {
    deleteOncallShift(shiftId).then(() => {
      onHide();
      onDelete();
    });
  }, [deleteOncallShift, shiftId, onHide, onDelete]);

  const handleCreate = useCallback(() => {
    if (shiftId === 'new') {
      createRotation(scheduleId, true, params).then(() => {
        onCreate();
      });
    } else {
      updateRotation(shiftId, params).then(() => {
        onUpdate();
      });
    }
  }, [scheduleId, shiftId, createRotation, updateRotation, onCreate, onUpdate, params]);

  const handleChange = useDebouncedCallback(updatePreview, 200);

  const isFormValid = useMemo(() => userGroups.some((group) => group.length), [userGroups]);

  useEffect(handleChange, [params]);

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
          <Text size="medium">{shiftId === 'new' ? 'New Override' : 'Update Override'}</Text>
          <HorizontalGroup>
            {shiftId !== 'new' && (
              <WithConfirm>
                <IconButton variant="secondary" tooltip="Delete" name="trash-alt" onClick={handleDeleteClick} />
              </WithConfirm>
            )}
            <IconButton variant="secondary" className={cx('drag-handler')} name="draggabledots" />
          </HorizontalGroup>
        </HorizontalGroup>
        <div className={cx('content')}>
          <VerticalGroup>
            <HorizontalGroup>
              <Field
                className={cx('date-time-picker')}
                label={
                  <Text type="primary" size="small">
                    Override start
                  </Text>
                }
              >
                <DateTimePicker value={shiftStart} onChange={setShiftStart} timezone={currentTimezone} />
              </Field>
              <Field
                className={cx('date-time-picker')}
                label={
                  <Text type="primary" size="small">
                    Override end
                  </Text>
                }
              >
                <DateTimePicker value={shiftEnd} onChange={setShiftEnd} timezone={currentTimezone} />
              </Field>
            </HorizontalGroup>
            <UserGroups
              value={userGroups}
              onChange={setUserGroups}
              isMultipleGroups={false}
              renderUser={renderUser}
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
            <Button variant="primary" onClick={handleCreate} disabled={!isFormValid}>
              {shiftId === 'new' ? 'Create' : 'Update'}
            </Button>
          </HorizontalGroup>
        </HorizontalGroup>
      </VerticalGroup>
    </Modal>
  );
};

export default ScheduleOverrideForm;
