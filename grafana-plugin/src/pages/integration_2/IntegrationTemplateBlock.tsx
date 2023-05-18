import React from 'react';

import { Button, HorizontalGroup, Icon, InlineLabel, LoadingPlaceholder, Tooltip } from '@grafana/ui';

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
      <Tooltip content={'Edit'}>
        <Button variant={'secondary'} icon={'edit'} tooltip="Edit" size={'md'} onClick={onEdit} />
      </Tooltip>
      <Tooltip content={'Reset Template to default'}>
        <Button variant={'secondary'} icon={'times'} size={'md'} onClick={onRemove} />
      </Tooltip>

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
