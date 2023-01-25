import React, { FC, useMemo } from 'react';

import cn from 'classnames/bind';
import { Link } from 'react-router-dom';

import Text from 'components/Text/Text';
import { getPathFromQueryParams } from 'utils/url';

import styles from './PluginLink.module.css';

interface PluginLinkProps {
  disabled?: boolean;
  className?: string;
  wrap?: boolean;
  children: any;
  query?: Record<string, any>;
}

const cx = cn.bind(styles);

const PluginLink: FC<PluginLinkProps> = (props) => {
  const { children, query, disabled, className, wrap = true } = props;

  const newPath = useMemo(() => getPathFromQueryParams(query), [query]);

  return disabled ? (
    <Text className={cx('root', className, { 'no-wrap': !wrap })} type="disabled">
      {children}
    </Text>
  ) : (
    <Link className={cx('root', className, { 'no-wrap': !wrap })} to={newPath}>
      {children}
    </Link>
  );
};

export default PluginLink;
