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
import { getTzOffsetString } from 'models/timezone/timezone.helpers';

import styles from './ScheduleOverrideForm.module.css';

interface RotationFormProps {
  layerId: string;
  onHide: () => void;
  id: number | 'new';
}

const cx = cn.bind(styles);

const ScheduleOverrideForm: FC<RotationFormProps> = (props) => {
  const { onHide } = props;

  const [shiftStart, setShiftStart] = useState<DateTime>(dateTime('2021-05-05 12:00:00'));
  const [shiftEnd, setShiftEnd] = useState<DateTime>(dateTime('2021-05-05 12:00:00'));

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
        <UserGroups />
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
            <Button variant="primary">Save</Button>
          </HorizontalGroup>
        </HorizontalGroup>
      </VerticalGroup>
    </Modal>
  );
};

export default ScheduleOverrideForm;
