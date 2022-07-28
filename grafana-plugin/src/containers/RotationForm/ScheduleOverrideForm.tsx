import React, { FC, useCallback, useState } from 'react';

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
import Draggable from 'react-draggable';

import Modal from 'components/Modal/Modal';
import Text from 'components/Text/Text';
import UserGroups from 'components/UserGroups/UserGroups';
import { Rotation, Schedule } from 'models/schedule/schedule.types';
import { getTzOffsetString } from 'models/timezone/timezone.helpers';
import { Timezone } from 'models/timezone/timezone.types';
import { User } from 'models/user/user.types';
import { getUTCString } from 'pages/schedule/Schedule.helpers';
import { useStore } from 'state/useStore';

import { RotationCreateData } from './RotationForm.types';

import styles from './RotationForm.module.css';

interface RotationFormProps {
  onHide: () => void;
  id: number | 'new';
  currentTimezone: Timezone;
  scheduleId: Schedule['id'];
  onCreate: () => void;
  onUpdate: () => void;
}

const cx = cn.bind(styles);

const ScheduleOverrideForm: FC<RotationFormProps> = (props) => {
  const { onHide, onCreate, currentTimezone, scheduleId, onUpdate } = props;

  const store = useStore();

  const [shiftStart, setShiftStart] = useState<DateTime>(dateTime('2022-07-26 12:00:00'));
  const [shiftEnd, setShiftEnd] = useState<DateTime>(dateTime('2022-07-26 20:00:00'));

  const [userGroups, setUserGroups] = useState([[]]);

  const getUser = (pk: User['pk']) => {
    return {
      name: store.userStore.items[pk]?.username,
      desc: store.userStore.items[pk]?.timezone,
    };
  };

  const handleCreate = useCallback(() => {
    store.scheduleStore
      .createRotation(scheduleId, true, {
        name: 'Rotation ' + Math.floor(Math.random() * 100),
        rotation_start: getUTCString(shiftStart),
        shift_start: getUTCString(shiftStart),
        shift_end: getUTCString(shiftEnd),
        rolling_users: userGroups,
        frequency: null,
      })
      .then(() => {
        onHide();
        onCreate();
      });
  }, [shiftStart, shiftEnd, userGroups]);

  const moment = dayjs();

  return (
    <Modal
      width="430px"
      title="New Rotation"
      onDismiss={onHide}
      contentElement={(props, children) => (
        <Draggable handle=".drag-handler" positionOffset={{ x: 0, y: 0 }}>
          <div {...props}>{children}</div>
        </Draggable>
      )}
    >
      <VerticalGroup>
        <HorizontalGroup justify="space-between">
          <Text size="medium">Rotation 1</Text>
          <HorizontalGroup>
            <IconButton variant="secondary" tooltip="Copy" name="copy" />
            <IconButton variant="secondary" tooltip="Code" name="brackets-curly" />
            <IconButton variant="secondary" tooltip="Delete" name="trash-alt" />
            <IconButton variant="secondary" className={cx('drag-handler')} name="draggabledots" />
          </HorizontalGroup>
        </HorizontalGroup>
        <UserGroups value={userGroups} onChange={setUserGroups} isMultipleGroups={false} getItemData={getUser} />
        {/*<hr />*/}
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
              <DateTimePicker date={shiftStart} onChange={setShiftStart} />
            </Field>
            <Field
              className={cx('date-time-picker')}
              label={
                <Text type="primary" size="small">
                  Override end
                </Text>
              }
            >
              <DateTimePicker date={shiftEnd} onChange={setShiftEnd} />
            </Field>
          </HorizontalGroup>
        </VerticalGroup>
        <HorizontalGroup justify="space-between">
          <Text type="secondary">Timezone: {getTzOffsetString(moment)}</Text>
          <HorizontalGroup>
            <Button variant="primary" onClick={handleCreate}>
              Save
            </Button>
          </HorizontalGroup>
        </HorizontalGroup>
      </VerticalGroup>
    </Modal>
  );
};

export default ScheduleOverrideForm;
