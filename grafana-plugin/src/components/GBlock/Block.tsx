import React, { FC, HTMLAttributes } from 'react';

import { cx } from '@emotion/css';
import { useStyles2 } from '@grafana/ui';
import { bem } from 'styles/utils.styles';

import { getBlockStyles } from './Block.styles';

interface BlockProps extends HTMLAttributes<HTMLElement> {
  bordered?: boolean;
  shadowed?: boolean;
  withBackground?: boolean;
  hover?: boolean;
  fullWidth?: boolean;
}

export const Block: FC<BlockProps> = (props) => {
  const {
    children,
    style,
    className,
    bordered = false,
    fullWidth = false,
    hover = false,
    shadowed = false,
    withBackground = false,
    ...rest
  } = props;

  const styles = useStyles2(getBlockStyles);

  return (
    <div
      className={cx(
        styles.root,
        {
          [bem(styles.root, 'bordered')]: bordered,
          [bem(styles.root, 'shadowed')]: shadowed,
          [bem(styles.root, 'fullWidth')]: fullWidth,
          [bem(styles.root, 'withBackGround')]: withBackground,
          [bem(styles.root, 'hover')]: hover,
        },
        className
      )}
      style={style}
      {...rest}
    >
      {children}
    </div>
  );
};
