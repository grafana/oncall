import React, { FC } from 'react';

import cn from 'classnames/bind';

import styles from 'components/Tag/Tag.module.css';

interface TagProps {
  color?: string;
  className?: string;
  border?: string;
  text?: string;
  children?: any;
  onClick?: (ev) => void;
  forwardedRef?: React.MutableRefObject<HTMLSpanElement>;
  size?: 'small' | 'medium';
}

const cx = cn.bind(styles);

export const Tag: FC<TagProps> = (props) => {
  const { children, color, text, className, border, onClick, size = 'medium' } = props;
  const style: React.CSSProperties = {};

  if (color) {
    style.backgroundColor = color;
  }

  if (text) {
    style.color = text;
  }

  if (border) {
    style.border = border;
  }

  return (
    <span style={style} className={cx('root', `size-${size}`, className)} onClick={onClick} ref={props.forwardedRef}>
      {children}
    </span>
  );
};
