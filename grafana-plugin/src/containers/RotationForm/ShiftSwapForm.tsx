import React, { useCallback, useEffect, useMemo, useState } from 'react';

import { Button, Field, HorizontalGroup, IconButton, Input, TextArea, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import Draggable from 'react-draggable';

import Modal from 'components/Modal/Modal';
import Tag from 'components/Tag/Tag';
import Text from 'components/Text/Text';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { SHIFT_SWAP_COLOR } from 'models/schedule/schedule.helpers';
import { Schedule, ShiftSwap } from 'models/schedule/schedule.types';
import { getTzOffsetString } from 'models/timezone/timezone.helpers';
import { Timezone } from 'models/timezone/timezone.types';
import { getUTCString } from 'pages/schedule/Schedule.helpers';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization';

import DateTimePicker from './parts/DateTimePicker';
import UserItem from './parts/UserItem';

import styles from './RotationForm.module.css';

const cx = cn.bind(styles);

interface ShiftSwapFormProps {
  id: ShiftSwap['id'] | 'new';
  scheduleId: Schedule['id'];
  params: Partial<ShiftSwap>;
  currentTimezone: Timezone;

  onUpdate: () => void;

  onHide: () => void;
}

const ShiftSwapForm = (props: ShiftSwapFormProps) => {
  const { onUpdate, onHide, id, scheduleId, params: defaultParams, currentTimezone } = props;

  const [shiftSwap, setShiftSwap] = useState({ ...defaultParams });

  const store = useStore();
  const { scheduleStore } = store;

  useEffect(() => {
    if (id !== 'new') {
      scheduleStore.loadShiftSwap(id).then(setShiftSwap);
    }
  }, [id]);

  useEffect(() => {
    if (defaultParams) {
      setShiftSwap({ ...shiftSwap, swap_start: defaultParams.swap_start, swap_end: defaultParams.swap_end });
    }
  }, [defaultParams]);

  const handleShiftSwapStartChange = useCallback(
    (value) => {
      setShiftSwap({ ...shiftSwap, swap_start: getUTCString(value) });
    },
    [shiftSwap]
  );

  const handleShiftSwapEndChange = useCallback(
    (value) => {
      setShiftSwap({ ...shiftSwap, swap_end: getUTCString(value) });
    },
    [shiftSwap]
  );

  const handleDescriptionChange = useCallback(
    (event) => {
      setShiftSwap({ ...shiftSwap, description: event.target.value });
    },
    [shiftSwap]
  );

  const handleCreate = useCallback(async () => {
    await scheduleStore.createShiftSwap({ schedule: scheduleId, ...shiftSwap });

    onHide();
    onUpdate();
  }, [shiftSwap]);

  const handleDelete = useCallback(async () => {
    await scheduleStore.deleteShiftSwap(id);

    onHide();
    onUpdate();
  }, [id]);

  const handleTake = useCallback(async () => {
    await scheduleStore.takeShiftSwap(id);

    onHide();
    onUpdate();
  }, [id]);

  const beneficiaryName = shiftSwap?.beneficiary && store.userStore.items[shiftSwap.beneficiary]?.name;

  const isNew = id === 'new';
  const isPastDue = useMemo(() => shiftSwap && dayjs(shiftSwap.swap_start).isBefore(dayjs()), [shiftSwap]);

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
              {isNew && <Tag color={SHIFT_SWAP_COLOR}>New</Tag>}
              <Text.Title level={5} editable>
                Shift swap
              </Text.Title>
            </HorizontalGroup>
            <HorizontalGroup>
              {!isNew && (
                <WithPermissionControlTooltip userAction={UserActions.SchedulesWrite}>
                  <WithConfirm title="Are you sure to delete shift swap request?" confirmText="Delete">
                    <IconButton variant="secondary" tooltip="Delete" name="trash-alt" onClick={handleDelete} />
                  </WithConfirm>
                </WithPermissionControlTooltip>
              )}
              <IconButton variant="secondary" className={cx('drag-handler')} name="draggabledots" />
              <IconButton name="times" variant="secondary" tooltip="Close" onClick={onHide} />
            </HorizontalGroup>
          </HorizontalGroup>

          <div className={cx('fields')}>
            {!isNew && (
              <Field label="Creator">
                <Input disabled value={beneficiaryName}></Input>
              </Field>
            )}

            <HorizontalGroup height="auto">
              <Field label="Swap start">
                <DateTimePicker
                  timezone={store.currentTimezone}
                  disabled={!isNew}
                  value={dayjs(shiftSwap.swap_start)}
                  onChange={handleShiftSwapStartChange}
                />
              </Field>
              <Field label="Swap end">
                <DateTimePicker
                  timezone={store.currentTimezone}
                  disabled={!isNew}
                  value={dayjs(shiftSwap.swap_end)}
                  onChange={handleShiftSwapEndChange}
                />
              </Field>
            </HorizontalGroup>

            <Field label="Description">
              <TextArea rows={4} disabled={!isNew} value={shiftSwap.description} onChange={handleDescriptionChange}>
                {shiftSwap.description}
              </TextArea>
            </Field>
            {!isNew && (
              <Field label="Taken by">
                {shiftSwap?.benefactor ? (
                  <UserItem
                    pk={shiftSwap?.benefactor}
                    shiftColor={SHIFT_SWAP_COLOR}
                    shiftStart={shiftSwap.swap_start}
                    shiftEnd={shiftSwap.swap_end}
                  />
                ) : (
                  <Text type="secondary">Not taken yet</Text>
                )}
              </Field>
            )}
          </div>

          <HorizontalGroup justify="space-between">
            <Text type="secondary">Current timezone: {getTzOffsetString(dayjs().tz(currentTimezone))}</Text>
            <HorizontalGroup>
              <WithPermissionControlTooltip userAction={UserActions.SchedulesWrite}>
                {isNew ? (
                  <Button variant="primary" onClick={handleCreate}>
                    Create
                  </Button>
                ) : (
                  <Button variant="primary" onClick={handleTake} disabled={Boolean(isPastDue || shiftSwap?.benefactor)}>
                    Take
                  </Button>
                )}
              </WithPermissionControlTooltip>
            </HorizontalGroup>
          </HorizontalGroup>
        </VerticalGroup>
      </div>
    </Modal>
  );
};

export default ShiftSwapForm;
