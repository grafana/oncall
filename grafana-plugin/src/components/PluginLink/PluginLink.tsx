import React, { FC, useCallback, useMemo } from 'react';

import { css, cx } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { useStyles2 } from '@grafana/ui';
import { Link } from 'react-router-dom';
import { bem } from 'styles/utils.styles';

import { getPathFromQueryParams } from 'utils/url';

interface PluginLinkProps {
  disabled?: boolean;
  className?: string;
  wrap?: boolean;
  children: any;
  query?: Record<string, any>;
  target?: string;
  onClick?: () => void;
}

export const PluginLink: FC<PluginLinkProps> = (props) => {
  const { children, query, disabled, className, wrap = true, target, onClick } = props;

  const styles = useStyles2(getStyles);
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
      className={cx(styles.root, className, { [styles.noWrap]: !wrap, [bem(styles.root, 'disabled')]: disabled })}
      to={newPath}
    >
      {children}
    </Link>
  );
};

const getStyles = (theme: GrafanaTheme2) => {
  return {
    root: css`
      color: ${theme.colors.primary.text};

      &--disabled {
        color: ${theme.colors.text.disabled};
      }
    `,

    noWrap: css`
      white-space: nowrap;
    `,
  };
};
