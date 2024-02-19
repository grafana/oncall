import React, { FC, useCallback, useMemo } from 'react';

import cn from 'classnames/bind';
import { Link } from 'react-router-dom';

import { getPathFromQueryParams } from 'utils/url';

import styles from './PluginLink.module.css';

interface PluginLinkProps {
  disabled?: boolean;
  className?: string;
  wrap?: boolean;
  children: any;
  query?: Record<string, any>;
  target?: string;
  onClick?: () => void;
}

const cx = cn.bind(styles);

export const PluginLink: FC<PluginLinkProps> = (props) => {
  const { children, query, disabled, className, wrap = true, target, onClick } = props;

  const newPath = useMemo(() => getPathFromQueryParams(query), [query]);

  const handleClick = useCallback(
    (event) => {
      event.stopPropagation();

      if (disabled || onClick) {
        event.preventDefault();
      }

      if (onClick) {
        onClick();
      }
    },
    [disabled, onClick]
  );

  return (
    <Link
      target={target}
      onClick={handleClick}
      className={cx('root', className, { 'no-wrap': !wrap, root_disabled: disabled })}
      to={newPath}
    >
      {children}
    </Link>
  );
};
