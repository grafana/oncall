import React, { FC } from 'react';

import cn from 'classnames/bind';

import styles from './Avatar.module.css';

interface AvatarProps {
  src: string;
  size: string;
  className?: string;
}

const cx = cn.bind(styles);

const Avatar: FC<AvatarProps> = ({ src, size, className, ...rest }) => {
  if (!src) {
    return null;
  }

  return <img src={src} className={cx('root', `avatarSize-${size}`, className)} data-testid="test__avatar" {...rest} />;
};

export default Avatar;
