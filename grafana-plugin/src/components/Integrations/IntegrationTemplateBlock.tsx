import React from 'react';

import { Button, InlineLabel, LoadingPlaceholder, Tooltip } from '@grafana/ui';
import cn from 'classnames/bind';

import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { UserActions } from 'utils/authorization';

import styles from './IntegrationTemplateBlock.module.scss';

const cx = cn.bind(styles);

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
  onEdit,
  onRemove,
  isLoading,
}) => {
  let inlineLabelProps = { labelTooltip };
  if (!labelTooltip) {
    delete inlineLabelProps.labelTooltip;
  }

  return (
    <div className={cx('container')}>
      <InlineLabel width={20} {...inlineLabelProps}>
        {label}
      </InlineLabel>
      <div className={cx('container__item')}>
        {renderInput()}
        <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
          <Tooltip content={'Edit'}>
            <Button variant={'secondary'} icon={'edit'} tooltip="Edit" size={'md'} onClick={onEdit} />
          </Tooltip>
        </WithPermissionControlTooltip>
        <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
          <Tooltip content={'Reset Template to default'}>
            <Button variant={'secondary'} icon={'times'} size={'md'} onClick={onRemove} />
          </Tooltip>
        </WithPermissionControlTooltip>

        {isLoading && <LoadingPlaceholder text="Loading..." />}
      </div>
    </div>
  );
};

export default IntegrationTemplateBlock;
