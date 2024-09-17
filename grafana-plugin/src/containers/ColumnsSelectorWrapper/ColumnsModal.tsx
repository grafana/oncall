import React, { useMemo, useState } from 'react';

import { css } from '@emotion/css';
import { LabelTag } from '@grafana/labels';
import {
  Button,
  Checkbox,
  IconButton,
  Input,
  LoadingPlaceholder,
  LoadingPlaceholder,
  Modal,
  Stack,
  useStyles2,
} from '@grafana/ui';
import { UserActions } from 'helpers/authorization/authorization';
import { PROCESSING_REQUEST_ERROR, StackSize } from 'helpers/consts';
import { WrapWithGlobalNotification } from 'helpers/decorators';
import { pluralize } from 'helpers/helpers';
import { useDebouncedCallback, useIsLoading } from 'helpers/hooks';
import { observer } from 'mobx-react';

import { Block } from 'components/GBlock/Block';
import { Text } from 'components/Text/Text';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { AlertGroupHelper } from 'models/alertgroup/alertgroup.helpers';
import { AlertGroupColumn, AlertGroupColumnType } from 'models/alertgroup/alertgroup.types';
import { ActionKey } from 'models/loader/action-keys';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { components } from 'network/oncall-api/autogenerated-api.types';
import { useStore } from 'state/useStore';

import { getColumnsSelectorWrapperStyles } from './ColumnsSelectorWrapper.styles';

interface ColumnsModalProps {
  isModalOpen: boolean;
  labelKeys: Array<ApiSchemas['LabelKey']>;
  setIsModalOpen: (value: boolean) => void;
  inputRef: React.RefObject<HTMLInputElement>;
}

interface SearchResult extends Pick<components['schemas']['LabelKey'], 'id' | 'name'> {
  isChecked: boolean;
  isCollapsed: boolean;
  values: any[];
}

const DEBOUNCE_MS = 300;

const loadingPlaceholderCSS = css`
  margin-bottom: 0;
  margin-right: 4px;
`;

export const ColumnsModal: React.FC<ColumnsModalProps> = observer(
  ({ isModalOpen, labelKeys, setIsModalOpen, inputRef }) => {
    const store = useStore();
    const styles = useStyles2(getColumnsSelectorWrapperStyles);

    const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
    const debouncedOnInputChange = useDebouncedCallback(onInputChange, DEBOUNCE_MS);

    const isLoading = useIsLoading(ActionKey.ADD_NEW_COLUMN_TO_ALERT_GROUP);
    const availableKeysForSearching = useMemo(() => {
      const cols = store.alertGroupStore.columns;
      return labelKeys.filter(
        (pair) => !cols.find((col) => col.id === pair.id && col.type === AlertGroupColumnType.LABEL)
      );
    }, [labelKeys, store.alertGroupStore.columns]);

    return (
      <Modal isOpen={isModalOpen} title={'Add column'} onDismiss={onCloseModal} closeOnEscape={false}>
        <Stack direction="column" gap={StackSize.md}>
          <div className={styles.content}>
            <Stack direction="column" gap={StackSize.md}>
              <Stack direction="column" gap={StackSize.xs}>
                <Input
                  className={styles.input}
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
              </Stack>

              {inputRef?.current?.value && searchResults.length && (
                <Stack direction="column" gap={StackSize.none}>
                  {searchResults.map((result, index) => (
                    <Stack direction="column" key={index}>
                      <div className={styles.fieldRow}>
                        <IconButton
                          aria-label={result.isCollapsed ? 'Expand' : 'Collapse'}
                          name={result.isCollapsed ? 'angle-right' : 'angle-down'}
                          onClick={() => expandOrCollapseSearchResultItem(result, index)}
                        />

                        <Checkbox
                          type="checkbox"
                          className={styles.checkboxAddOption}
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
                        <Block bordered withBackground fullWidth className={styles.valuesBlock}>
                          {result.values === undefined ? (
                            <LoadingPlaceholder text="Loading..." className={loadingPlaceholderCSS} />
                          ) : (
                            renderLabelValues(result.name, result.values)
                          )}
                        </Block>
                      )}
                    </Stack>
                  ))}
                </Stack>
              )}

              {inputRef?.current?.value && searchResults.length === 0 && (
                <Text type="primary">0 results for your search.</Text>
              )}
            </Stack>
          </div>

          <Stack justifyContent="flex-end" gap={StackSize.md}>
            <Button variant="secondary" onClick={onCloseModal}>
              Close
            </Button>
            <WithPermissionControlTooltip userAction={UserActions.OtherSettingsWrite}>
              <Button
                disabled={isLoading || !searchResults.find((it) => it.isChecked)}
                variant="primary"
                onClick={WrapWithGlobalNotification(onAddNewColumns, {
                  success: 'New column has been added to the list.',
                  failure: PROCESSING_REQUEST_ERROR,
                })}
              >
                {isLoading ? <LoadingPlaceholder className={loadingPlaceholderCSS} text="Loading..." /> : 'Add'}
              </Button>
            </WithPermissionControlTooltip>
          </Stack>
        </Stack>
      </Modal>
    );

    function renderLabelValues(keyName: string, values: Array<ApiSchemas['LabelValue']>) {
      return (
        <Stack gap={StackSize.xs}>
          {values.slice(0, 2).map((val) => (
            <LabelTag label={keyName} value={val.name} key={val.id} />
          ))}
          <div>{values.length > 2 ? `+ ${values.length - 2}` : ``}</div>
        </Stack>
      );
    }

    async function expandOrCollapseSearchResultItem(result: SearchResult, index: number) {
      setSearchResults((items) =>
        items.map((it, idx) => (idx === index ? { ...it, isCollapsed: !it.isCollapsed } : it))
      );

      await fetchLabelValues(result, index);
    }

    async function fetchLabelValues(result: SearchResult, index: number) {
      const labelResponse = await AlertGroupHelper.loadValuesForLabelKey(result.id);

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
            (item): AlertGroupColumn => ({
              id: item.id,
              name: item.name,
              isVisible: false,
              type: AlertGroupColumnType.LABEL,
            })
          ),
      ];

      const columns: { visible: AlertGroupColumn[]; hidden: AlertGroupColumn[] } = {
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
