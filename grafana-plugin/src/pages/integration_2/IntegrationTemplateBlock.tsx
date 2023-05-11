import React from 'react';

import { Button, HorizontalGroup, Icon, InlineLabel, LoadingPlaceholder } from '@grafana/ui';

import Text from 'components/Text/Text';

interface IntegrationTemplateBlockProps {
  label: string;
  labelTooltip?: string;
  renderInput: () => React.ReactNode;
  showHelp?: boolean;
  isLoading?: boolean;

  onEdit: (templateName) => void;
  onRemove?: () => void;
  onHelp?: () => void;
}

const IntegrationTemplateBlock: React.FC<IntegrationTemplateBlockProps> = ({
  label,
  labelTooltip,
  renderInput,
  showHelp,
  onEdit,
  onHelp,
  onRemove,
  isLoading,
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
      <Button variant={'secondary'} icon={'edit'} tooltip="Edit" size={'md'} onClick={onEdit} />
      <Button variant={'secondary'} icon={'times'} size={'md'} tooltip="Reset Template to default" onClick={onRemove} />

      {showHelp && (
        <Button variant="secondary" size="md" onClick={onHelp}>
          <Text type="link">Help</Text>
          <Icon name="angle-down" size="sm" />
        </Button>
      )}

      {isLoading && <LoadingPlaceholder text="Loading..." />}
    </HorizontalGroup>
  );
};

export default IntegrationTemplateBlock;
