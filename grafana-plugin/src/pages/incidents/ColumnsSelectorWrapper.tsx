import React, { useEffect, useRef, useState } from 'react';

import { Button, Checkbox, HorizontalGroup, Icon, Input, Modal, Toggletip, VerticalGroup } from '@grafana/ui';

import Text from 'components/Text/Text';

import { ColumnsSelector } from './ColumnsSelector';
import { useStore } from 'state/useStore';
import { useDebouncedCallback } from 'utils/hooks';
import { Label } from 'models/label/label.types';
import { noop } from 'lodash-es';

import cn from 'classnames/bind';

import styles from 'pages/incidents/ColumnsSelector.module.scss';

const cx = cn.bind(styles);

interface ColumnsSelectorWrapperProps {}

const DEBOUNCE_MS = 300;

const ColumnsSelectorWrapper: React.FC<ColumnsSelectorWrapperProps> = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const [searchResults, setSearchResults] = useState<Label[]>([]);
  const [labelKeys, setLabelKeys] = useState<Label[]>([]);

  const inputRef = useRef<HTMLInputElement>(null);

  const debouncedOnInputChange = useDebouncedCallback(onInputChange, DEBOUNCE_MS);

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
      <Modal isOpen={isModalOpen} title={'Add field'} onDismiss={() => setIsModalOpen(false)}>
        <VerticalGroup spacing="md">
          <Input autoFocus placeholder="Search..." ref={inputRef} onChange={debouncedOnInputChange} />

          {inputRef?.current?.value === '' && (
            <Text type="primary">{labelKeys.length} items available. Type in to see suggestions</Text>
          )}

          {searchResults.length && (
            <VerticalGroup spacing="xs">
              {searchResults.map((result) => (
                <HorizontalGroup spacing="md">
                  <Checkbox type="checkbox" value={true} onChange={noop} />

                  <div className={cx('result-spacer')}>
                    <Icon name="tag-alt" />
                  </div>

                  <Text type="primary">{result.name}</Text>
                </HorizontalGroup>
              ))}
            </VerticalGroup>
          )}

          <HorizontalGroup justify="flex-end" spacing="md">
            <Button
              variant="secondary"
              onClick={() => {
                setIsModalOpen(false);
                setTimeout(() => forceOpenToggletip(), 0);
              }}
            >
              Close
            </Button>
            <Button variant="primary">Add</Button>
          </HorizontalGroup>
        </VerticalGroup>
      </Modal>

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

  function forceOpenToggletip() {
    document.getElementById('toggletip-button')?.click();
  }

  function onInputChange() {
    const search = inputRef?.current?.value;
    setSearchResults(labelKeys.filter((pair) => pair.name.indexOf(search) > -1));
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
};

export default ColumnsSelectorWrapper;
