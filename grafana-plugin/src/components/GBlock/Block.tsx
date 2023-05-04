import React, { FC, HTMLAttributes } from 'react';

import cn from 'classnames/bind';

import styles from './Block.module.scss';

interface BlockProps extends HTMLAttributes<HTMLElement> {
  bordered?: boolean;
  shadowed?: boolean;
  withBackground?: boolean;
  hover?: boolean;
  fullWidth?: boolean;
}

const cx = cn.bind(styles);

const Block: FC<BlockProps> = (props) => {
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

  return (
    <div
      className={cx(
        'root',
        {
          root_bordered: bordered,
          root_shadowed: shadowed,
          'root--fullWidth': fullWidth,
          'root--withBackGround': withBackground,
          'root--hover': hover,
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

export default Block;
