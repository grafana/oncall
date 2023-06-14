import React from 'react';

import { Button, InlineLabel, LoadingPlaceholder, Tooltip } from '@grafana/ui';
import cn from 'classnames/bind';

import styles from './IntegrationTemplateBlock.module.scss';

const cx = cn.bind(styles);

interface IntegrationTemplateBlockProps {
  label: string;
  labelTooltip?: string;
  isTemplateEditable: boolean;
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
  isTemplateEditable,
  renderInput,
  onEdit,
  onRemove,
  isLoading,
}) => {
  let tooltip = labelTooltip;
  let inlineLabelProps = { tooltip };
  if (!tooltip) {
    delete inlineLabelProps.tooltip;
  }

  return (
    <div className={cx('container')}>
      <InlineLabel width={20} {...inlineLabelProps}>
        {label}
      </InlineLabel>
      <div className={cx('container__item')}>
        {renderInput()}
        {isTemplateEditable && (
          <>
            <Tooltip content={'Edit'}>
              <Button variant={'secondary'} icon={'edit'} tooltip="Edit" size={'md'} onClick={onEdit} />
            </Tooltip>
            <Tooltip content={'Reset Template to default'}>
              <Button variant={'secondary'} icon={'times'} size={'md'} onClick={onRemove} />
            </Tooltip>
          </>
        )}

        {isLoading && <LoadingPlaceholder text="Loading..." />}
      </div>
    </div>
  );
};

export default IntegrationTemplateBlock;
