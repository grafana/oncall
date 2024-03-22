import React, { FC } from 'react';

import { css } from '@emotion/css';
import { Button as GrafanaButton, ButtonProps as GrafanaButtonProps, useStyles2 } from '@grafana/ui';
import cn from 'classnames';

interface ButtonProps extends GrafanaButtonProps {
  showAsLink?: boolean;
}

export const Button: FC<ButtonProps> = ({ showAsLink, ...props }) => {
  const styles = useStyles2(getStyles);

  return (
    <GrafanaButton
      {...props}
      className={cn({ [styles.asLink]: showAsLink }, props.className)}
      fill={showAsLink ? 'text' : props.fill}
    />
  );
};

const getStyles = () => ({
  asLink: css`
    &,
    &:hover {
      background: none;
      display: inline;
      height: unset;
      padding: 0;
      border: none;
    }
  `,
});
