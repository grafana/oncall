import React, { FC } from 'react';

import cn from 'classnames/bind';

import styles from 'components/Tag/Tag.module.css';

interface TagProps {
  color: string;
  className?: string;
  children?: any;
  onClick?: (ev) => void;
  forwardedRef?: React.MutableRefObject<HTMLSpanElement>;
}

const cx = cn.bind(styles);

const Tag: FC<TagProps> = (props) => {
  const { children, color, className, onClick } = props;

  return (
    <span
      style={{ backgroundColor: color }}
      className={cx('root', className)}
      onClick={onClick}
      ref={props.forwardedRef}
    >
      {children}
    </span>
  );
};

export default Tag;
