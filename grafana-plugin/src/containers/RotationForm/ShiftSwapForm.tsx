import React, { useCallback, useEffect, useMemo, useState } from 'react';

import { css, cx } from '@emotion/css';
import { Button, Field, IconButton, Input, TextArea, Stack, useStyles2 } from '@grafana/ui';
import dayjs from 'dayjs';
import { UserActions } from 'helpers/authorization/authorization';
import { GRAFANA_HEADER_HEIGHT, StackSize } from 'helpers/consts';
import { useDebouncedCallback, useResize } from 'helpers/hooks';
import Draggable, { DraggableData, DraggableEvent } from 'react-draggable';

import { Modal } from 'components/Modal/Modal';
import { Tag } from 'components/Tag/Tag';
import { Text } from 'components/Text/Text';
import { WithConfirm } from 'components/WithConfirm/WithConfirm';
import { calculateScheduleFormOffset } from 'containers/Rotations/Rotations.helpers';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { SHIFT_SWAP_COLOR } from 'models/schedule/schedule.helpers';
import { Schedule, ShiftSwap } from 'models/schedule/schedule.types';
import { getUTCString } from 'pages/schedule/Schedule.helpers';
import { useStore } from 'state/useStore';

import { getDraggableModalCoordinatesOnInit } from './RotationForm.helpers';
import { DateTimePicker } from './parts/DateTimePicker';
import { UserItem } from './parts/UserItem';

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
  const [offsetTop, setOffsetTop] = useState(GRAFANA_HEADER_HEIGHT + 10);
  const [draggablePosition, setDraggablePosition] = useState<{ x: number; y: number }>(undefined);
  const [bounds, setDraggableBounds] = useState<{ left: number; right: number; top: number; bottom: number }>(
    undefined
  );

  const debouncedOnResize = useDebouncedCallback(onResize, 250);

  useResize(debouncedOnResize);

  const store = useStore();
  const {
    scheduleStore,
    userStore: { currentUserPk },
    timezoneStore: { selectedTimezoneOffset },
  } = store;

  useEffect(() => {
    (async () => {
      setOffsetTop(await calculateScheduleFormOffset(`.${cx('draggable')}`));
    })();
  }, []);

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
  }, [shiftSwap, store.timezoneStore.calendarStartDate, selectedTimezoneOffset]);

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

  const styles = useStyles2(getStyles);

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
        <Draggable
          handle=".drag-handler"
          defaultClassName="draggable"
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
      <div className={styles.root}>
        <Stack direction="column">
          <Stack justifyContent="space-between">
            <Stack gap={StackSize.sm}>
              {isNew && <Tag color={SHIFT_SWAP_COLOR}>New</Tag>}
              <Text.Title level={5}>{isNew ? 'Shift swap request' : 'Shift swap'}</Text.Title>
            </Stack>
            <Stack>
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
            </Stack>
          </Stack>

          <div className={styles.fields}>
            {!isNew && (
              <Field label="Requested by">
                <Input disabled value={beneficiaryName}></Input>
              </Field>
            )}

            <Stack height="auto">
              <Field label="Swap start">
                <DateTimePicker
                  disabled={!isNew}
                  utcOffset={selectedTimezoneOffset}
                  value={dayjs(shiftSwap.swap_start)}
                  onChange={handleShiftSwapStartChange}
                />
              </Field>
              <Field label="Swap end">
                <DateTimePicker
                  disabled={!isNew}
                  utcOffset={selectedTimezoneOffset}
                  value={dayjs(shiftSwap.swap_end)}
                  onChange={handleShiftSwapEndChange}
                />
              </Field>
            </Stack>

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

          <Stack justifyContent="space-between">
            <Text type="secondary">Current timezone: {store.timezoneStore.selectedTimezoneLabel}</Text>
            <Stack>
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
            </Stack>
          </Stack>
        </Stack>
      </div>
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

    const bounds = getDraggableModalCoordinatesOnInit(data, offsetTop);
    setDraggableBounds(bounds);
  }
};

const getStyles = () => {
  return {
    root: css`
      display: block;
      width: 100%;
    `,

    fields: css`
      width: 100%;
    `,
  };
};
