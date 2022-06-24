import React, { FC } from 'react';

import { IconButton, VerticalGroup, HorizontalGroup, Field, Input, Button } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import Draggable from 'react-draggable';

import Modal from 'components/Modal/Modal';
import Text from 'components/Text/Text';
import UserGroups from 'components/UserGroups/UserGroups';
import { getTzOffsetString } from 'models/timezone/timezone.helpers';

import styles from './RotationForm.module.css';

interface RotationFormProps {
  layerId: string;
  onHide: () => void;
  id: number | 'new';
}

const cx = cn.bind(styles);

const RotationForm: FC<RotationFormProps> = (props) => {
  const { onHide } = props;

  const moment = dayjs();

  return (
    <Modal
      width="400px"
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
        <hr />
        <VerticalGroup>
          <HorizontalGroup>
            <Field label="Repeat shifts every">
              <Input value="1" />
            </Field>
            <Field label="">
              <Input value="days" />
            </Field>
          </HorizontalGroup>
          <HorizontalGroup>
            <Field label="Shift start">
              <Input value="12 May, 22  10:00" />
            </Field>
            <Field label="Shift end">
              <Input value="12 May, 22  10:00" />
            </Field>
          </HorizontalGroup>
          <HorizontalGroup>
            <Field label="Rotation start">
              <Input value="12 May, 22  10:00" />
            </Field>
            <Field label="Rotation end">
              <Input value="endless" />
            </Field>
          </HorizontalGroup>
        </VerticalGroup>
        <HorizontalGroup justify="space-between">
          <Text type="secondary">Timezone: {getTzOffsetString(moment)}</Text>
          <HorizontalGroup>
            <Button variant="secondary">+ Override</Button>
            <Button variant="primary">Create</Button>
          </HorizontalGroup>
        </HorizontalGroup>
      </VerticalGroup>
    </Modal>
  );
};

export default RotationForm;
