import React from 'react';

import { Button, InlineLabel, LoadingPlaceholder } from '@grafana/ui';
import cn from 'classnames/bind';

import { WithConfirm } from 'components/WithConfirm/WithConfirm';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { UserActions } from 'utils/authorization/authorization';

import styles from './IntegrationTemplateBlock.module.scss';

const cx = cn.bind(styles);

interface IntegrationTemplateBlockProps {
  label: string;
  labelTooltip?: string;
  isTemplateEditable: boolean;
  renderInput: () => React.ReactNode;
  showHelp?: boolean;
  isLoading?: boolean;
  warningOnEdit?: string;

  onEdit: (templateName) => void;
  onRemove?: () => void;
  onHelp?: () => void;
}

export const IntegrationTemplateBlock: React.FC<IntegrationTemplateBlockProps> = ({
  label,
  labelTooltip,
  isTemplateEditable,
  renderInput,
  onEdit,
  onRemove,
  isLoading,
  warningOnEdit,
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
            <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
              <WithConfirm skip={!warningOnEdit} title="" body={warningOnEdit} confirmText="Edit">
                <Button variant={'secondary'} icon="edit" tooltip="Edit" size="md" onClick={onEdit} />
              </WithConfirm>
            </WithPermissionControlTooltip>
            <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
              <WithConfirm
                title=""
                body={`Are you sure you want to reset the ${label} template to its default state?`}
                confirmText="Reset"
              >
                <Button
                  variant="secondary"
                  icon="times"
                  size="md"
                  tooltip="Reset template to default"
                  onClick={onRemove}
                />
              </WithConfirm>
            </WithPermissionControlTooltip>
          </>
        )}

        {isLoading && <LoadingPlaceholder text="Loading..." />}
      </div>
    </div>
  );
};
