import React, { ReactElement, useCallback } from 'react';

import { css, cx } from '@emotion/css';
import { Tooltip } from '@grafana/ui';
import { isUserActionAllowed, UserAction } from 'helpers/authorization/authorization';
import { observer } from 'mobx-react';

interface WithPermissionControlTooltipProps {
  userAction: UserAction;
  children: ReactElement;
  className?: string;
}

export const WithPermissionControlTooltip = observer((props: WithPermissionControlTooltipProps) => {
  const { userAction, children, className } = props;

  const disabledByPermissions = !isUserActionAllowed(userAction);

  const onClickCallback = useCallback(
    (event: any) => {
      if (children.props.onClick) {
        children.props.onClick(event);
      }
    },
    [children.props]
  );

  return (
    <>
      {disabledByPermissions ? (
        <Tooltip
          content={'You do not have permission to perform this action. Ask an admin to upgrade your permissions.'}
          placement="top"
        >
          <div
            className={cx(
              css`
                display: inline;
              `,
              className
            )}
          >
            {React.cloneElement(children, {
              disabled: children.props.disabled || disabledByPermissions,
              onClick: onClickCallback,
            })}
          </div>
        </Tooltip>
      ) : (
        children
      )}
    </>
  );
});
