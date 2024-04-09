import React, { FC } from 'react';

import { cx } from '@emotion/css';
import { useStyles2 } from '@grafana/ui';
import { bem } from 'styles/utils.styles';

import { getAvatarStyles } from './Avatar.styles';

interface AvatarProps {
  src: string;
  size: 'xs' | 'small' | 'medium' | 'large';
  className?: string;
}

export const Avatar: FC<AvatarProps> = (props) => {
  const { src, size, className, ...rest } = props;

  const styles = useStyles2(getAvatarStyles);

  if (!src) {
    return null;
  }

  return (
    <img
      src={src}
      className={cx(styles.avatar, bem(styles.avatar, size), className)}
      data-testid="test__avatar"
      {...rest}
    />
  );
};
