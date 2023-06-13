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
}

const cx = cn.bind(styles);

const PluginLink: FC<PluginLinkProps> = (props) => {
  const { children, query, disabled, className, wrap = true, target } = props;

  const newPath = useMemo(() => getPathFromQueryParams(query), [query]);

  const handleClick = useCallback(
    (event) => {
      event.stopPropagation();

      if (disabled) {
        event.preventDefault();
      }
    },
    [disabled]
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

export default PluginLink;
