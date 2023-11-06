import React, { useState } from 'react';

import { Button, HorizontalGroup, Icon, Input, Modal, Toggletip, VerticalGroup } from '@grafana/ui';
import { noop } from 'lodash-es';

import Text from 'components/Text/Text';

import { ColumnsSelector } from './ColumnsSelector';

interface ColumnsSelectorWrapperProps {}

const ColumnsSelectorWrapper: React.FC<ColumnsSelectorWrapperProps> = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <>
      <Modal isOpen={isModalOpen} title={'Add field'} onDismiss={() => setIsModalOpen(false)}>
        <VerticalGroup spacing="md">
          <Input autoFocus placeholder="Search..." value="" onChange={noop} />

          <Text type="primary">2101 items available. Type in to see suggestions</Text>

          <HorizontalGroup justify="flex-end" spacing="md">
            <Button variant="secondary">Close</Button>
            <Button variant="primary">Add</Button>
          </HorizontalGroup>
        </VerticalGroup>
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
