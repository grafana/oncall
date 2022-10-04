import React, { useCallback, FC } from 'react';

import { getLocationSrv } from '@grafana/runtime';
import { LocationUpdate } from '@grafana/runtime/services/LocationSrv';
import cn from 'classnames/bind';
import qs from 'query-string';

import styles from './PluginLink.module.css';

interface PluginLinkProps extends LocationUpdate {
  disabled?: boolean;
  className?: string;
  wrap?: boolean;
  children: any;
}

const cx = cn.bind(styles);

const PluginLink: FC<PluginLinkProps> = (props) => {
  const { children, partial = false, path = '/a/grafana-oncall-app/', query, disabled, className, wrap = true } = props;

  const href = `${path}?${qs.stringify(query)}`;

  const onClickCallback = useCallback(
    (event) => {
      event.preventDefault();

      // @ts-ignore
      if (children.props?.disabled) {
        return;
      }

      !disabled && getLocationSrv().update({ partial, path, query });
    },
    [children]
  );

  return (
    <a
      href={href}
      onClick={onClickCallback}
      className={cx('root', className, { root_disabled: disabled, 'no-wrap': !wrap })}
    >
      {children}
    </a>
  );
};

export default PluginLink;
