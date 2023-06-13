import React, { FC } from 'react';

import cn from 'classnames/bind';

import styles from 'components/Tag/Tag.module.css';

interface TagProps {
  color?: string;
  className?: string;
  border?: string;
  children?: any;
  onClick?: (ev) => void;
  forwardedRef?: React.MutableRefObject<HTMLSpanElement>;
}

const cx = cn.bind(styles);

const Tag: FC<TagProps> = (props) => {
  const { children, color, className, border, onClick } = props;
  const style: React.CSSProperties = {};

  if (color) {
    style.backgroundColor = color;
  }

  if (border) {
    style.border = border;
  }

  return (
    <span style={style} className={cx('root', className)} onClick={onClick} ref={props.forwardedRef}>
      {children}
    </span>
  );
};

export default Tag;
