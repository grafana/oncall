import React, { ReactElement, useCallback } from 'react';

import { Tooltip } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import { isUserActionAllowed, UserAction } from 'utils/authorization';

import styles from './WithPermissionControlTooltip.module.css';

const cx = cn.bind(styles);

interface WithPermissionControlTooltipProps {
  userAction: UserAction;
  children: ReactElement;
  disableByPaywall?: boolean;
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
          <div className={cx('wrapper', className)}>
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
