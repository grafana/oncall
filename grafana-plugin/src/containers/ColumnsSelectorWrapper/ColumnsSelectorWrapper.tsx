import React, { useEffect, useRef, useState } from 'react';

import { useStyles2, Button, HorizontalGroup, Icon, LoadingPlaceholder, Modal, VerticalGroup } from '@grafana/ui';
import { observer } from 'mobx-react';

import { Text } from 'components/Text/Text';
import { ColumnsSelector, convertColumnsToTableSettings } from 'containers/ColumnsSelector/ColumnsSelector';
import { getColumnsSelectorWrapperStyles } from 'containers/ColumnsSelectorWrapper/ColumnsSelectorWrapper.styles';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { AlertGroupHelper } from 'models/alertgroup/alertgroup.helpers';
import { AlertGroupColumn } from 'models/alertgroup/alertgroup.types';
import { ActionKey } from 'models/loader/action-keys';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization/authorization';
import { WrapAutoLoadingState, WrapWithGlobalNotification } from 'utils/decorators';
import { useIsLoading } from 'utils/hooks';

import { ColumnsModal } from './ColumnsModal';

interface ColumnsSelectorWrapperProps {}

export const ColumnsSelectorWrapper: React.FC<ColumnsSelectorWrapperProps> = observer(() => {
  const [isConfirmRemovalModalOpen, setIsConfirmRemovalModalOpen] = useState(false);
  const [columnToBeRemoved, setColumnToBeRemoved] = useState<AlertGroupColumn>(undefined);
  const [isColumnAddModalOpen, setIsColumnAddModalOpen] = useState(false);
  const [isFloatingDisplayOpen, setIsFloatingDisplayOpen] = useState(false);
  const [labelKeys, setLabelKeys] = useState<Array<ApiSchemas['LabelKey']>>([]);
  const isRemoveLoading = useIsLoading(ActionKey.REMOVE_COLUMN_FROM_ALERT_GROUP);

  const inputRef = useRef<HTMLInputElement>(null);
  const wrappingFloatingContainerRef = useRef<HTMLDivElement>(null);

  const styles = useStyles2(getColumnsSelectorWrapperStyles);

  const store = useStore();

  useEffect(() => {
    isColumnAddModalOpen &&
      (async function () {
        const keys = await AlertGroupHelper.loadLabelsKeys();
        setLabelKeys(keys);
      })();
  }, [isColumnAddModalOpen]);

  useEffect(() => {
    document.addEventListener('click', onFloatingDisplayClick);

    return () => {
      document.removeEventListener('click', onFloatingDisplayClick);
    };
  }, []);

  return (
    <>
      <ColumnsModal
        inputRef={inputRef}
        isModalOpen={isColumnAddModalOpen}
        labelKeys={labelKeys}
        setIsModalOpen={setIsColumnAddModalOpen}
      />

      <Modal
        closeOnEscape={false}
        isOpen={isConfirmRemovalModalOpen}
        title={'Remove column'}
        onDismiss={onConfirmRemovalClose}
        className={styles.removalModal}
      >
        <VerticalGroup spacing="lg">
          <Text type="primary">Are you sure you want to remove column {columnToBeRemoved?.name}?</Text>

          <HorizontalGroup justify="flex-end" spacing="md">
            <Button variant={'secondary'} onClick={onConfirmRemovalClose}>
              Cancel
            </Button>
            <WithPermissionControlTooltip userAction={UserActions.OtherSettingsWrite}>
              <Button
                disabled={isRemoveLoading}
                variant={'destructive'}
                onClick={WrapAutoLoadingState(
                  WrapWithGlobalNotification(onColumnRemovalClick, {
                    success: 'Column has been removed from the list.',
                    failure: 'There was an error processing your request. Please try again',
                  }),
                  ActionKey.REMOVE_COLUMN_FROM_ALERT_GROUP
                )}
              >
                {isRemoveLoading ? <LoadingPlaceholder text="Loading..." className="loadingPlaceholder" /> : 'Remove'}
              </Button>
            </WithPermissionControlTooltip>
          </HorizontalGroup>
        </VerticalGroup>
      </Modal>

      <div ref={wrappingFloatingContainerRef}>
        {!isColumnAddModalOpen && !isConfirmRemovalModalOpen ? (
          <div className={styles.floatingContainer}>
            {renderToggletipButton()}
            <div
              className={[styles.floatingContent, isFloatingDisplayOpen ? styles.floatingContentVisible : ''].join(' ')}
            >
              <ColumnsSelector
                onColumnAddModalOpen={() => setIsColumnAddModalOpen(!isColumnAddModalOpen)}
                onConfirmRemovalModalOpen={(column: AlertGroupColumn) => {
                  setIsConfirmRemovalModalOpen(!isConfirmRemovalModalOpen);
                  setColumnToBeRemoved(column);
                }}
              />
            </div>
          </div>
        ) : (
          renderToggletipButton()
        )}
      </div>
    </>
  );

  function onFloatingDisplayClick(event) {
    const element = wrappingFloatingContainerRef.current;
    const isInside = element?.contains(event.target as HTMLDivElement);

    if (!isInside) {
      setIsFloatingDisplayOpen(false);
    }
  }

  function onConfirmRemovalClose(): void {
    setIsConfirmRemovalModalOpen(false);
    forceOpenToggletip();
  }

  async function onColumnRemovalClick(): Promise<void> {
    await store.alertGroupStore.removeTableColumn(columnToBeRemoved, convertColumnsToTableSettings);

    setIsConfirmRemovalModalOpen(false);
    forceOpenToggletip();
  }

  function renderToggletipButton() {
    return (
      <Button
        type="button"
        variant={'secondary'}
        icon="columns"
        id="toggletip-button"
        onClick={() => setIsFloatingDisplayOpen(!isFloatingDisplayOpen)}
      >
        <HorizontalGroup spacing="xs">
          Columns
          <Icon name="angle-down" />
        </HorizontalGroup>
      </Button>
    );
  }
});

function forceOpenToggletip() {
  document.getElementById('toggletip-button')?.click();
}
