import React, { ChangeEvent, useCallback, useState } from 'react';

import { Stack, Modal as GrafanaModal, Button, InlineSwitch, useStyles2 } from '@grafana/ui';
import { StackSize } from 'helpers/consts';
import { useIsLoading } from 'helpers/hooks';

import { Text } from 'components/Text/Text';
import { getRotationFormStyles } from 'containers/RotationForm/RotationForm.styles';
import { ActionKey } from 'models/loader/action-keys';

interface DeletionModalProps {
  onHide: () => void;
  onConfirm: (force: boolean) => void;
}

export const DeletionModal = ({ onHide, onConfirm }: DeletionModalProps) => {
  const [isForceDelete, setIsForceDelete] = useState<boolean>(false);
  const isDeleting = useIsLoading(ActionKey.DELETE_ONCALL_SHIFT);

  const styles = useStyles2(getRotationFormStyles);

  const handleIsForceDeleteChange = useCallback((event: ChangeEvent<HTMLInputElement>) => {
    setIsForceDelete(event.target.checked);
  }, []);

  const handleConfirmClick = useCallback(() => {
    onConfirm(isForceDelete);
  }, [isForceDelete]);

  return (
    <GrafanaModal isOpen onDismiss={onHide} title="Delete rotation" className={styles.confirmationModal}>
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
          <Button variant="destructive" onClick={handleConfirmClick} disabled={isDeleting}>
            Delete
          </Button>
        </Stack>
      </Stack>
    </GrafanaModal>
  );
};
