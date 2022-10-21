import React, { FC } from 'react';

import cn from 'classnames/bind';

import styles from 'components/Tag/Tag.module.css';

interface TagProps {
  color: string;
  className?: string;
  children?: any;
}

const cx = cn.bind(styles);

const Tag: FC<TagProps> = ({ children, color, className }) => (
  <span style={{ backgroundColor: color }} className={cx('root', className)}>
    {children}
  </span>
);

export default Tag;
