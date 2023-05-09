import React from 'react';

import { Button, HorizontalGroup, Icon, InlineLabel } from '@grafana/ui';

import Text from 'components/Text/Text';

interface IntegrationTemplateBlockProps {
  label: string;
  labelTooltip?: string;
  renderInput: () => React.ReactNode;
  showClose?: boolean;
  showHelp?: boolean;

  onEdit: (templateName) => void;
  onRemove?: () => void;
  onHelp?: () => void;
}

const IntegrationTemplateBlock: React.FC<IntegrationTemplateBlockProps> = ({
  label,
  labelTooltip,
  renderInput,
  showClose,
  showHelp,
  onEdit,
  onHelp,
  onRemove,
}) => {
  let inlineLabelProps = { labelTooltip };
  if (!labelTooltip) {
    delete inlineLabelProps.labelTooltip;
  }

  return (
    <HorizontalGroup align={'flex-start'} spacing={'xs'}>
      <InlineLabel width={20} {...inlineLabelProps}>
        {label}
      </InlineLabel>
      {renderInput()}
      <Button variant={'secondary'} icon={'edit'} size={'md'} onClick={onEdit} />
      {showClose && <Button variant={'secondary'} icon={'times'} size={'md'} onClick={onRemove} />}
      {showHelp && (
        <Button variant="secondary" size="md" onClick={onHelp}>
          <Text type="link">Help</Text>
          <Icon name="angle-down" size="sm" />
        </Button>
      )}
    </HorizontalGroup>
  );
};

export default IntegrationTemplateBlock;
