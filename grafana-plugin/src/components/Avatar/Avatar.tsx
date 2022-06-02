import React, { FC } from 'react';

import cn from 'classnames/bind';

import styles from './Avatar.module.css';

interface AvatarProps {
  src: string;
  size: string;
  className?: string;
}

const cx = cn.bind(styles);

const Avatar: FC<AvatarProps> = (props) => {
  const { src, size, className } = props;

  if (!src) {
    return null;
  }

  return <img src={src} className={cx('root', `avatarSize-${size}`, className)} />;
};

export default Avatar;
