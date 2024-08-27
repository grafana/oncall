import React, { ChangeEvent, useCallback, useState } from 'react';

import { Stack, Modal as GrafanaModal, Button, InlineSwitch } from '@grafana/ui';
import cn from 'classnames/bind';

import { Text } from 'components/Text/Text';
import { StackSize } from 'utils/consts';

import styles from 'containers/RotationForm/RotationForm.module.css';

const cx = cn.bind(styles);

interface DeletionModalProps {
  onHide: () => void;
  onConfirm: (force: boolean) => void;
}

export const DeletionModal = ({ onHide, onConfirm }: DeletionModalProps) => {
  const [isForceDelete, setIsForceDelete] = useState<boolean>(false);

  const handleIsForceDeleteChange = useCallback((event: ChangeEvent<HTMLInputElement>) => {
    setIsForceDelete(event.target.checked);
  }, []);

  const handleConfirmClick = useCallback(() => {
    onConfirm(isForceDelete);
  }, [isForceDelete]);

  return (
    <GrafanaModal isOpen onDismiss={onHide} title="Delete rotation" className={cx('confirmation-modal')}>
      <Stack direction="column" gap={StackSize.lg}>
        <Stack direction="column">
          <Text type="secondary">
            This schedule is in use. As result the action will delete all shifts in the rotation which are greater than
            current timestamp. All past shifts will remain in the schedule.
          </Text>
        </Stack>

        <InlineSwitch
          transparent
          showLabel
          label="Delete past shifts"
          value={isForceDelete}
          onChange={handleIsForceDeleteChange}
        />

        <Stack justifyContent="flex-end">
          <Button variant="secondary" onClick={onHide}>
            Cancel
          </Button>
          <Button variant="destructive" onClick={handleConfirmClick}>
            Delete
          </Button>
        </Stack>
      </Stack>
    </GrafanaModal>
  );
};
