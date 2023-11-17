import React, { useEffect, useRef, useState } from 'react';

import {
  Button,
  Checkbox,
  HorizontalGroup,
  Icon,
  Input,
  LoadingPlaceholder,
  Modal,
  Toggletip,
  VerticalGroup,
} from '@grafana/ui';
import cn from 'classnames/bind';

import Text from 'components/Text/Text';
import { ColumnsSelector, convertColumnsToTableSettings } from 'containers/ColumnsSelector/ColumnsSelector';
import styles from 'containers/ColumnsSelectorWrapper/ColumnsSelectorWrapper.module.scss';
import { AGColumn, AGColumnType } from 'models/alertgroup/alertgroup.types';
import { Label } from 'models/label/label.types';
import { useStore } from 'state/useStore';
import { useDebouncedCallback } from 'utils/hooks';
import LoaderStore from 'models/loader/loader';
import { ActionKey } from 'models/loader/action-keys';
import { observer } from 'mobx-react';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { UserActions } from 'utils/authorization';

const cx = cn.bind(styles);

interface ColumnsSelectorWrapperProps {}

const DEBOUNCE_MS = 300;

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
      >
        <VerticalGroup spacing="md">
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

interface ColumnsModalProps {
  isModalOpen: boolean;
  labelKeys: Label[];
  setIsModalOpen: (value: boolean) => void;
  inputRef: React.RefObject<HTMLInputElement>;
}

interface SearchResult extends Label {
  isChecked: boolean;
}

const ColumnsModal: React.FC<ColumnsModalProps> = observer(({ isModalOpen, labelKeys, setIsModalOpen, inputRef }) => {
  const store = useStore();
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const debouncedOnInputChange = useDebouncedCallback(onInputChange, DEBOUNCE_MS);

  const isLoading = LoaderStore.isLoading(ActionKey.IS_ADDING_NEW_COLUMN_TO_ALERT_GROUP);

  return (
    <Modal isOpen={isModalOpen} title={'Add column'} onDismiss={onCloseModal} closeOnEscape={false}>
      <VerticalGroup spacing="md">
        <div className={cx('content')}>
          <VerticalGroup spacing="md">
            <Input
              className={cx('input')}
              autoFocus
              placeholder="Search..."
              ref={inputRef}
              onChange={debouncedOnInputChange}
            />

            {inputRef?.current?.value === '' && (
              <Text type="primary">{labelKeys.length} items available. Type to see suggestions</Text>
            )}

            {inputRef?.current?.value && searchResults.length && (
              <VerticalGroup spacing="xs">
                {searchResults.map((result, index) => (
                  <div key={index} className={cx('field-row')}>
                    <Checkbox
                      type="checkbox"
                      value={result.isChecked}
                      onChange={() => {
                        setSearchResults((items) => {
                          return items.map((item) => {
                            const updatedItem: SearchResult = { ...item, isChecked: !item.isChecked };
                            return item.id === result.id ? updatedItem : item;
                          });
                        });
                      }}
                    />

                    <Text type="primary">{result.name}</Text>
                  </div>
                ))}
              </VerticalGroup>
            )}

            {inputRef?.current?.value && searchResults.length === 0 && (
              <Text type="primary">0 results for your search.</Text>
            )}
          </VerticalGroup>
        </div>

        <HorizontalGroup justify="flex-end" spacing="md">
          <Button variant="secondary" onClick={onCloseModal}>
            Close
          </Button>
          <WithPermissionControlTooltip userAction={UserActions.OtherSettingsWrite}>
            <Button
              disabled={isLoading || !searchResults.find((it) => it.isChecked)}
              variant="primary"
              onClick={onAddNewColumns}
            >
              {isLoading ? <LoadingPlaceholder className={'loader'} text="Loading..." /> : 'Add'}
            </Button>
          </WithPermissionControlTooltip>
        </HorizontalGroup>
      </VerticalGroup>
    </Modal>
  );

  function onCloseModal() {
    inputRef.current.value = '';

    setSearchResults([]);
    setIsModalOpen(false);
    setTimeout(() => forceOpenToggletip(), 0);
  }

  async function onAddNewColumns() {
    const mergedColumns = [
      ...store.alertGroupStore.columns,
      ...searchResults
        .filter((item) => item.isChecked)
        .map(
          (it): AGColumn => ({
            id: it.id,
            name: it.name,
            isVisible: false,
            type: AGColumnType.LABEL,
          })
        ),
    ];

    const columns: { visible: AGColumn[]; hidden: AGColumn[] } = {
      visible: mergedColumns.filter((col) => col.isVisible),
      hidden: mergedColumns.filter((col) => !col.isVisible),
    };

    await store.alertGroupStore.updateTableSettings(columns, false);
    await store.alertGroupStore.fetchTableSettings();

    setIsModalOpen(false);
    setTimeout(() => forceOpenToggletip(), 0);
    setSearchResults([]);

    inputRef.current.value = '';
  }

  function onInputChange() {
    const search = inputRef?.current?.value;
    setSearchResults(
      labelKeys.filter((pair) => pair.name.indexOf(search) > -1).map((pair) => ({ ...pair, isChecked: false }))
    );
  }
});

function forceOpenToggletip() {
  document.getElementById('toggletip-button')?.click();
}

export default ColumnsSelectorWrapper;
