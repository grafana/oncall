import { Button, HorizontalGroup, Icon, Modal, Toggletip } from '@grafana/ui';
import React, { useState } from 'react';
import { ColumnsSelector } from './ColumnsSelector';

interface ColumnsSelectorWrapperProps {}

const ColumnsSelectorWrapper: React.FC<ColumnsSelectorWrapperProps> = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <>
      <Modal isOpen={isModalOpen} title={'Add field'} onDismiss={() => setIsModalOpen(false)}>
        <HorizontalGroup align="flex-end" spacing="xs">
          <Button variant="secondary">Close</Button>
          <Button variant="primary">Add</Button>
        </HorizontalGroup>
      </Modal>

      {!isModalOpen ? (
        <Toggletip
          content={<ColumnsSelector onModalOpen={() => setIsModalOpen(!isModalOpen)} />}
          placement={'bottom-end'}
          closeButton={true}
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
      <Button type="button" variant={'secondary'} icon="columns">
        <HorizontalGroup spacing="xs">
          Fields
          <Icon name="angle-down" />
        </HorizontalGroup>
      </Button>
    );
  }
};

export default ColumnsSelectorWrapper;
