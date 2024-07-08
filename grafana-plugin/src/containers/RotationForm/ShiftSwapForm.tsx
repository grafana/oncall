import React, { useCallback, useEffect, useMemo, useState } from 'react';

import { Button, Field, HorizontalGroup, IconButton, Input, TextArea, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import Draggable from 'react-draggable';

import { Modal } from 'components/Modal/Modal';
import { Tag } from 'components/Tag/Tag';
import { Text } from 'components/Text/Text';
import { WithConfirm } from 'components/WithConfirm/WithConfirm';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { SHIFT_SWAP_COLOR } from 'models/schedule/schedule.helpers';
import { Schedule, ShiftSwap } from 'models/schedule/schedule.types';
import { getUTCString } from 'pages/schedule/Schedule.helpers';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization/authorization';

import { DateTimePicker } from './parts/DateTimePicker';
import { UserItem } from './parts/UserItem';

import styles from './RotationForm.module.css';

const cx = cn.bind(styles);

interface ShiftSwapFormProps {
  id: ShiftSwap['id'] | 'new';
  scheduleId: Schedule['id'];
  params: Partial<ShiftSwap>;
  onUpdate: () => void;
  onHide: () => void;
}

export const ShiftSwapForm = (props: ShiftSwapFormProps) => {
  const { onUpdate, onHide, id, scheduleId, params: defaultParams } = props;

  const [shiftSwap, setShiftSwap] = useState({ ...defaultParams });

  const store = useStore();
  const {
    scheduleStore,
    userStore: { currentUserPk },
  } = store;

  useEffect(() => {
    (async () => {
      if (id !== 'new') {
        const shiftSwap = await scheduleStore.loadShiftSwap(id);
        setShiftSwap(shiftSwap);
      }
    })();
  }, [id]);

  const handleHide = useCallback(() => {
    scheduleStore.clearPreview();

    onHide();
  }, []);

  useEffect(() => {
    if (defaultParams) {
      setShiftSwap({ ...shiftSwap, swap_start: defaultParams.swap_start, swap_end: defaultParams.swap_end });
    }
  }, [defaultParams]);

  const handleShiftSwapStartChange = useCallback(
    (value) => {
      const diff = dayjs(shiftSwap.swap_end).diff(dayjs(shiftSwap.swap_start));

      setShiftSwap({ ...shiftSwap, swap_start: getUTCString(value), swap_end: getUTCString(value.add(diff)) });
    },
    [shiftSwap]
  );

  const handleShiftSwapEndChange = useCallback(
    (value) => {
      setShiftSwap({ ...shiftSwap, swap_end: getUTCString(value) });
    },
    [shiftSwap]
  );

  useEffect(() => {
    if (id === 'new') {
      store.scheduleStore.updateShiftsSwapPreview(scheduleId, store.timezoneStore.calendarStartDate, {
        id: 'new',
        beneficiary: { pk: currentUserPk },
        ...shiftSwap,
      });
    }
  }, [shiftSwap, store.timezoneStore.calendarStartDate, store.timezoneStore.selectedTimezoneOffset]);

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

  const beneficiaryName = shiftSwap?.beneficiary?.display_name;

  const isNew = id === 'new';
  const isPastDue = useMemo(() => shiftSwap && dayjs(shiftSwap.swap_start).isBefore(dayjs()), [shiftSwap]);

  return (
    <Modal
      top="0"
      isOpen
      width="430px"
      onDismiss={handleHide}
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
              <Text.Title level={5}>{isNew ? 'Shift swap request' : 'Shift swap'}</Text.Title>
            </HorizontalGroup>
            <HorizontalGroup>
              {!isNew && (
                <WithPermissionControlTooltip userAction={UserActions.SchedulesWrite}>
                  <WithConfirm title="Are you sure to delete shift swap request?" confirmText="Delete">
                    <IconButton
                      variant="secondary"
                      tooltip="Delete"
                      name="trash-alt"
                      onClick={handleDelete}
                      disabled={shiftSwap.beneficiary?.pk !== currentUserPk}
                    />
                  </WithConfirm>
                </WithPermissionControlTooltip>
              )}
              <IconButton aria-label="Drag" variant="secondary" className={cx('drag-handler')} name="draggabledots" />
              <IconButton name="times" variant="secondary" tooltip="Close" onClick={handleHide} />
            </HorizontalGroup>
          </HorizontalGroup>

          <div className={cx('fields')}>
            {!isNew && (
              <Field label="Requested by">
                <Input disabled value={beneficiaryName}></Input>
              </Field>
            )}

            <HorizontalGroup height="auto">
              <Field label="Swap start">
                <DateTimePicker
                  disabled={!isNew}
                  value={dayjs(shiftSwap.swap_start)}
                  onChange={handleShiftSwapStartChange}
                />
              </Field>
              <Field label="Swap end">
                <DateTimePicker
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
              <Field label="Swapped by">
                {shiftSwap?.benefactor ? (
                  <UserItem
                    pk={shiftSwap?.benefactor.pk}
                    shiftColor={SHIFT_SWAP_COLOR}
                    shiftStart={shiftSwap.swap_start}
                    shiftEnd={shiftSwap.swap_end}
                  />
                ) : (
                  <Text type="secondary">Not accepted yet</Text>
                )}
              </Field>
            )}
          </div>

          <HorizontalGroup justify="space-between">
            <Text type="secondary">Current timezone: {store.timezoneStore.selectedTimezoneLabel}</Text>
            <HorizontalGroup>
              <WithPermissionControlTooltip userAction={UserActions.SchedulesWrite}>
                {isNew ? (
                  <Button variant="primary" onClick={handleCreate}>
                    Create
                  </Button>
                ) : (
                  <Button
                    variant="primary"
                    onClick={handleTake}
                    disabled={Boolean(
                      isPastDue || shiftSwap?.benefactor || shiftSwap.beneficiary?.pk === currentUserPk
                    )}
                  >
                    Accept
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
