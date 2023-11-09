import React, { useEffect, useRef, useState } from 'react';

import { Button, Checkbox, HorizontalGroup, Icon, Input, Modal, Toggletip, VerticalGroup } from '@grafana/ui';

import Text from 'components/Text/Text';

import { ColumnsSelector } from './ColumnsSelector';
import { useStore } from 'state/useStore';
import { useDebouncedCallback } from 'utils/hooks';
import { Label } from 'models/label/label.types';

import cn from 'classnames/bind';

import styles from 'pages/incidents/ColumnsSelector.module.scss';
import { AGColumn } from 'models/alertgroup/alertgroup.types';

const cx = cn.bind(styles);

interface ColumnsSelectorWrapperProps {}

const DEBOUNCE_MS = 300;

const ColumnsSelectorWrapper: React.FC<ColumnsSelectorWrapperProps> = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const [labelKeys, setLabelKeys] = useState<Label[]>([]);

  const inputRef = useRef<HTMLInputElement>(null);

  const store = useStore();

  useEffect(() => {
    isModalOpen &&
      (async function () {
        const keys = await store.alertGroupStore.loadLabelsKeys();
        setLabelKeys(keys);
      })();
  }, [isModalOpen]);

  return (
    <>
      <ColumnsModal
        inputRef={inputRef}
        isModalOpen={isModalOpen}
        labelKeys={labelKeys}
        setIsModalOpen={setIsModalOpen}
      />

      {!isModalOpen ? (
        <Toggletip
          content={<ColumnsSelector onModalOpen={() => setIsModalOpen(!isModalOpen)} />}
          placement={'bottom-end'}
          show={true}
          closeButton={false}
        >
          {renderToggletipButton()}
        </Toggletip>
      ) : (
        renderToggletipButton()
      )}
    </>
  );

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

const ColumnsModal: React.FC<ColumnsModalProps> = ({ isModalOpen, labelKeys, setIsModalOpen, inputRef }) => {
  const store = useStore();
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const debouncedOnInputChange = useDebouncedCallback(onInputChange, DEBOUNCE_MS);

  return (
    <Modal isOpen={isModalOpen} title={'Add field'} onDismiss={() => setIsModalOpen(false)}>
      <VerticalGroup spacing="md">
        <Input
          className={cx('input')}
          autoFocus
          placeholder="Search..."
          ref={inputRef}
          onChange={debouncedOnInputChange}
        />

        {inputRef?.current?.value === '' && (
          <Text type="primary">{labelKeys.length} items available. Type in to see suggestions</Text>
        )}

        {searchResults.length && (
          <VerticalGroup spacing="xs">
            {searchResults.map((result) => (
              <HorizontalGroup spacing="md">
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
              </HorizontalGroup>
            ))}
          </VerticalGroup>
        )}

        {inputRef?.current?.value && searchResults.length === 0 && (
          <Text type="primary">0 results for your search.</Text>
        )}

        <HorizontalGroup justify="flex-end" spacing="md">
          <Button
            variant="secondary"
            onClick={() => {
              inputRef.current.value = '';

              setSearchResults([]);
              setIsModalOpen(false);
              setTimeout(() => forceOpenToggletip(), 0);
            }}
          >
            Close
          </Button>
          <Button variant="primary" onClick={onAddNewColumns}>
            Add
          </Button>
        </HorizontalGroup>
      </VerticalGroup>
    </Modal>
  );

  function onAddNewColumns() {
    const newColumns: AGColumn[] = searchResults
      .filter((item) => item.isChecked)
      .map((it) => ({
        id: it.id,
        name: it.name,
        isVisible: true,
      }));

    store.alertGroupStore.columns = [...store.alertGroupStore.columns, ...newColumns];

    setIsModalOpen(false);
    setTimeout(() => forceOpenToggletip(), 0);
    setSearchResults([]);

    inputRef.current.value = '';
  }

  function forceOpenToggletip() {
    document.getElementById('toggletip-button')?.click();
  }

  function onInputChange() {
    const search = inputRef?.current?.value;
    setSearchResults(
      labelKeys.filter((pair) => pair.name.indexOf(search) > -1).map((pair) => ({ ...pair, isChecked: false }))
    );
  }
};

export default ColumnsSelectorWrapper;
