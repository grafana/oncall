import React, { useEffect, useRef, useState } from 'react';

import { Button, HorizontalGroup, Icon, Modal, Toggletip, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';

import Text from 'components/Text/Text';
import { ColumnsSelector, convertColumnsToTableSettings } from 'containers/ColumnsSelector/ColumnsSelector';
import styles from 'containers/ColumnsSelectorWrapper/ColumnsSelectorWrapper.module.scss';
import { AGColumn } from 'models/alertgroup/alertgroup.types';
import { Label } from 'models/label/label.types';
import { useStore } from 'state/useStore';

import { ColumnsModal } from './ColumnsModal';

const cx = cn.bind(styles);

interface ColumnsSelectorWrapperProps {}

const ColumnsSelectorWrapper: React.FC<ColumnsSelectorWrapperProps> = () => {
  const [isConfirmRemovalModalOpen, setIsConfirmRemovalModalOpen] = useState(false);
  const [columnToBeRemoved, setColumnToBeRemoved] = useState<AGColumn>(undefined);
  const [isColumnAddModalOpen, setIsColumnAddModalOpen] = useState(false);

  const [labelKeys, setLabelKeys] = useState<Label[]>([]);

  const inputRef = useRef<HTMLInputElement>(null);

  const store = useStore();

  useEffect(() => {
    isColumnAddModalOpen &&
      (async function () {
        const keys = await store.alertGroupStore.loadLabelsKeys();
        setLabelKeys(keys);
      })();
  }, [isColumnAddModalOpen]);

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
        className={cx('removal-modal')}
      >
        <VerticalGroup spacing="lg">
          <Text type="primary">Are you sure you want to remove column label {columnToBeRemoved?.name}?</Text>

          <HorizontalGroup justify="flex-end" spacing="md">
            <Button variant={'secondary'} onClick={onConfirmRemovalClose}>
              Cancel
            </Button>
            <Button variant={'destructive'} onClick={onColumnRemovalClick}>
              Remove
            </Button>
          </HorizontalGroup>
        </VerticalGroup>
      </Modal>

      {!isColumnAddModalOpen && !isConfirmRemovalModalOpen ? (
        <Toggletip
          content={
            <ColumnsSelector
              onColumnAddModalOpen={() => setIsColumnAddModalOpen(!isColumnAddModalOpen)}
              onConfirmRemovalModalOpen={(column: AGColumn) => {
                setIsConfirmRemovalModalOpen(!isConfirmRemovalModalOpen);
                setColumnToBeRemoved(column);
              }}
            />
          }
          placement={'bottom-end'}
          show={true}
          closeButton={false}
          onClose={onToggletipClose}
        >
          {renderToggletipButton()}
        </Toggletip>
      ) : (
        renderToggletipButton()
      )}
    </>
  );

  function onConfirmRemovalClose(): void {
    setIsConfirmRemovalModalOpen(false);
    forceOpenToggletip();
  }

  async function onColumnRemovalClick(): Promise<void> {
    const columns = store.alertGroupStore.columns.filter((col) => col.id !== columnToBeRemoved.id);

    await store.alertGroupStore.updateTableSettings(convertColumnsToTableSettings(columns), false);
    await store.alertGroupStore.fetchTableSettings();

    setIsConfirmRemovalModalOpen(false);
    forceOpenToggletip();
  }

  function renderToggletipButton() {
    return (
      <Button type="button" variant={'secondary'} icon="columns" id="toggletip-button">
        <HorizontalGroup spacing="xs">
          Fields
          <Icon name="angle-down" />
        </HorizontalGroup>
      </Button>
    );
  }

  function onToggletipClose() {
    const { alertGroupStore } = store;

    // reset temporary cached columns
    alertGroupStore.temporaryColumns = [...alertGroupStore.columns];
  }
};

function forceOpenToggletip() {
  document.getElementById('toggletip-button')?.click();
}

export default ColumnsSelectorWrapper;
