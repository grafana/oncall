import React from 'react';

import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { Button, InlineLabel, LoadingPlaceholder, useStyles2 } from '@grafana/ui';

import { WithConfirm } from 'components/WithConfirm/WithConfirm';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { UserActions } from 'utils/authorization/authorization';

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
  const styles = useStyles2(getStyles);

  let tooltip = labelTooltip;
  let inlineLabelProps = { tooltip };
  if (!tooltip) {
    delete inlineLabelProps.tooltip;
  }

  return (
    <div className={styles.container}>
      <InlineLabel width={20} {...inlineLabelProps}>
        {label}
      </InlineLabel>
      <div className={styles.item}>
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

const getStyles = (_theme: GrafanaTheme2) => {
  return {
    container: css`
      display: flex;
      flex-direction: row;
      gap: 4px;

      label {
        margin-right: 0;
      }
    `,

    item: css`
      flex-grow: 1;
      white-space: nowrap;
      overflow: hidden;
      display: flex;
      flex-direction: row;
      gap: 4px;
    `,
  };
};
