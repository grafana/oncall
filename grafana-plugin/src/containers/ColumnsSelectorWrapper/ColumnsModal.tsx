import React, { useMemo, useState } from 'react';

import { LabelTag } from '@grafana/labels';
import {
  Button,
  Checkbox,
  HorizontalGroup,
  IconButton,
  Input,
  LoadingPlaceholder,
  Modal,
  VerticalGroup,
} from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import Block from 'components/GBlock/Block';
import Text from 'components/Text/Text';
import styles from 'containers/ColumnsSelectorWrapper/ColumnsSelectorWrapper.module.scss';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { AGColumn, AGColumnType } from 'models/alertgroup/alertgroup.types';
import { Label, LabelValue } from 'models/label/label.types';
import { ActionKey } from 'models/loader/action-keys';
import { LoaderStore } from 'models/loader/loader';
import { useStore } from 'state/useStore';
import { openErrorNotification, pluralize } from 'utils';
import { UserActions } from 'utils/authorization';
import { useDebouncedCallback } from 'utils/hooks';

const cx = cn.bind(styles);

interface ColumnsModalProps {
  isModalOpen: boolean;
  labelKeys: Label[];
  setIsModalOpen: (value: boolean) => void;
  inputRef: React.RefObject<HTMLInputElement>;
}

interface SearchResult extends Label {
  isChecked: boolean;
  isCollapsed: boolean;
  values: any[];
}

const DEBOUNCE_MS = 300;

export const ColumnsModal: React.FC<ColumnsModalProps> = observer(
  ({ isModalOpen, labelKeys, setIsModalOpen, inputRef }) => {
    const store = useStore();
    const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
    const debouncedOnInputChange = useDebouncedCallback(onInputChange, DEBOUNCE_MS);

    const isLoading = LoaderStore.isLoading(ActionKey.IS_ADDING_NEW_COLUMN_TO_ALERT_GROUP);

    const availableKeysForSearching = useMemo(() => {
      const currentAGColumns = store.alertGroupStore.columns.map((col) => col.name);
      return labelKeys.filter((pair) => currentAGColumns.indexOf(pair.name) === -1);
    }, [labelKeys, store.alertGroupStore.columns]);

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
                <Text type="primary">
                  {availableKeysForSearching.length} {pluralize('item', availableKeysForSearching.length)} available.
                  Type to see suggestions
                </Text>
              )}

              {inputRef?.current?.value && searchResults.length && (
                <VerticalGroup spacing="xs">
                  {searchResults.map((result, index) => (
                    <VerticalGroup>
                      <div key={index} className={cx('field-row')}>
                        <IconButton
                          aria-label={result.isCollapsed ? 'Expand' : 'Collapse'}
                          name={result.isCollapsed ? 'angle-down' : 'angle-right'}
                          onClick={() => expandOrCollapseSearchResultItem(result, index)}
                        />

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
                      {!result.isCollapsed && (
                        <Block bordered withBackground fullWidth className={cx('values-block')}>
                          {result.values === undefined ? (
                            <LoadingPlaceholder text="Loading..." className="loadingPlaceholder" />
                          ) : (
                            renderLabelValues(result.name, result.values)
                          )}
                        </Block>
                      )}
                    </VerticalGroup>
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

    function renderLabelValues(keyName: string, values: LabelValue[]) {
      return (
        <HorizontalGroup spacing="xs">
          {values.slice(0, 2).map((val) => (
            <LabelTag label={keyName} value={val.name} key={val.id} />
          ))}
          <div className={cx('total-values-count')}>{values.length > 2 ? `+ ${values.length - 2}` : ``}</div>
        </HorizontalGroup>
      );
    }

    async function expandOrCollapseSearchResultItem(result: SearchResult, index: number) {
      setSearchResults((items) =>
        items.map((it, idx) => (idx === index ? { ...it, isCollapsed: !it.isCollapsed } : it))
      );

      await fetchLabelValues(result, index);
    }

    async function fetchLabelValues(result: SearchResult, index: number) {
      const labelResponse = await store.alertGroupStore.loadValuesForLabelKey(result.id);

      setSearchResults((items) =>
        items.map((it, idx) => (idx === index ? { ...it, values: labelResponse.values } : it))
      );
    }

    function onCloseModal() {
      inputRef.current.value = '';

      setSearchResults([]);
      setIsModalOpen(false);
      setTimeout(forceOpenToggletip, 0);
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

      try {
        await store.alertGroupStore.updateTableSettings(columns, false);
        await store.alertGroupStore.fetchTableSettings();

        setIsModalOpen(false);
        setTimeout(() => forceOpenToggletip(), 0);
        setSearchResults([]);

        inputRef.current.value = '';
      } catch (ex) {
        openErrorNotification('An error has occurred. Please try again');
      }
    }

    function onInputChange() {
      const search = inputRef?.current?.value;

      setSearchResults(
        availableKeysForSearching
          .filter((pair) => pair.name.indexOf(search) > -1)
          .map((pair) => ({ ...pair, isChecked: false, isCollapsed: true, values: undefined }))
      );
    }

    function forceOpenToggletip() {
      document.getElementById('toggletip-button')?.click();
    }
  }
);
