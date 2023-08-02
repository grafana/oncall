import React, { useCallback, useEffect, useMemo, useState } from 'react';

import { dateTime } from '@grafana/data';
import {
  Button,
  DateTimePicker,
  Field,
  HorizontalGroup,
  IconButton,
  Input,
  TextArea,
  VerticalGroup,
} from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import Draggable from 'react-draggable';

import Modal from 'components/Modal/Modal';
import Text from 'components/Text/Text';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { Schedule, ShiftSwap } from 'models/schedule/schedule.types';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization';

import styles from './RotationForm.module.css';

const cx = cn.bind(styles);

interface ShiftSwapFormProps {
  id: ShiftSwap['id'] | 'new';
  scheduleId: Schedule['id'];
  params: Partial<ShiftSwap>;

  onUpdate: () => void;

  onHide: () => void;
}

const ShiftSwapForm = (props: ShiftSwapFormProps) => {
  const { onUpdate, onHide, id, scheduleId, params: defaultParams } = props;

  const [shiftSwap, setShiftSwap] = useState({ ...defaultParams });

  const store = useStore();
  const { scheduleStore } = store;

  const allowDelete = true;

  useEffect(() => {
    if (id !== 'new') {
      scheduleStore.loadShiftSwap(id).then(setShiftSwap);
    }
  }, [id]);

  const isShiftSwapInThePast = useMemo(() => shiftSwap && dayjs(shiftSwap.swap_start).isBefore(dayjs()), [shiftSwap]);

  const handleCreate = useCallback(() => {
    scheduleStore.createShiftSwap({ schedule: scheduleId, ...shiftSwap });

    onHide();
    onUpdate();
  }, [shiftSwap]);

  const handleDelete = useCallback(() => {
    scheduleStore.deleteShiftSwap(id);

    onHide();
    onUpdate();
  }, [id]);

  const handleTake = useCallback(() => {
    scheduleStore.takeShiftSwap(id);

    onHide();
    onUpdate();
  }, [id]);

  const beneficiaryName = shiftSwap?.beneficiary && store.userStore.items[shiftSwap.beneficiary]?.name;
  const benefactorName = shiftSwap?.benefactor && store.userStore.items[shiftSwap.benefactor]?.name;

  return (
    <Modal
      top="0"
      isOpen
      width="430px"
      onDismiss={onHide}
      contentElement={(props, children) => (
        <Draggable handle=".drag-handler" defaultClassName={cx('draggable')} positionOffset={{ x: 0, y: 200 }}>
          <div {...props}>{children}</div>
        </Draggable>
      )}
    >
      <div className={cx('root')}>
        <VerticalGroup>
          <HorizontalGroup justify="space-between">
            <HorizontalGroup spacing="sm">
              <Text.Title level={5} editable>
                {id === 'new' ? 'New' : ''} Shift swap
              </Text.Title>
            </HorizontalGroup>
            <HorizontalGroup>
              <IconButton
                disabled={!allowDelete}
                variant="secondary"
                tooltip="Delete"
                name="trash-alt"
                //onClick={() => setShowDeleteRotationConfirmation(true)}
              />
              <IconButton variant="secondary" className={cx('drag-handler')} name="draggabledots" />
              <IconButton name="times" variant="secondary" tooltip="Close" onClick={onHide} />
            </HorizontalGroup>
          </HorizontalGroup>

          <div className={cx('fields')}>
            <Field label="Creator">
              <Input disabled value={beneficiaryName}></Input>
            </Field>

            <HorizontalGroup height="auto">
              <Field disabled label="Swap start">
                <DateTimePicker disabled date={dateTime(shiftSwap.swap_start)} />
              </Field>
              <Field disabled label="Swap end">
                <DateTimePicker disabled date={dateTime(shiftSwap.swap_end)} />
              </Field>
            </HorizontalGroup>

            <Field label="Description">
              <TextArea disabled>{shiftSwap.description}</TextArea>
            </Field>

            <Field label="Taken by">
              <Input disabled value={benefactorName}></Input>
            </Field>
          </div>

          <HorizontalGroup justify="space-between">
            <Text type="secondary"></Text>
            <HorizontalGroup>
              {id !== 'new' && (
                <WithPermissionControlTooltip userAction={UserActions.SchedulesWrite}>
                  <WithConfirm title="Are you sure to delete shift swap request?" confirmText="Delete">
                    <Button variant="destructive" onClick={handleDelete}>
                      Delete
                    </Button>
                  </WithConfirm>
                </WithPermissionControlTooltip>
              )}
              {id === 'new' ? (
                <WithPermissionControlTooltip userAction={UserActions.SchedulesWrite}>
                  <Button variant="primary" onClick={handleCreate}>
                    Request
                  </Button>
                </WithPermissionControlTooltip>
              ) : (
                <WithPermissionControlTooltip userAction={UserActions.SchedulesWrite}>
                  <Button
                    variant="primary"
                    onClick={handleTake}
                    disabled={Boolean(isShiftSwapInThePast || shiftSwap?.benefactor)}
                  >
                    Take
                  </Button>
                </WithPermissionControlTooltip>
              )}
            </HorizontalGroup>
          </HorizontalGroup>
        </VerticalGroup>
      </div>
    </Modal>
  );
};

export default ShiftSwapForm;
