import React, { FC, HTMLAttributes } from 'react';

import cn from 'classnames/bind';

import styles from './Block.module.css';

interface BlockProps extends HTMLAttributes<HTMLElement> {
  bordered?: boolean;
  shadowed?: boolean;
  withBackground?: boolean;
}

const cx = cn.bind(styles);

const Block: FC<BlockProps> = (props) => {
  const { children, style, className, bordered = false, shadowed = false, withBackground = false, ...rest } = props;

  return (
    <div
      className={cx('root', className, {
        root_bordered: bordered,
        root_shadowed: shadowed,
        'root_with-background': withBackground,
      })}
      style={style}
      {...rest}
    >
      {children}
    </div>
  );
};

export default Block;
