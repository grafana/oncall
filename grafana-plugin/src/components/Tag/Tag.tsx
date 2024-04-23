import React, { FC } from 'react';

import { css, cx } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { useStyles2, useTheme2 } from '@grafana/ui';
import { bem } from 'styles/utils.styles';
import tinycolor from 'tinycolor2';

interface TagProps {
  color?: string | TagColor;
  className?: string;
  border?: string;
  text?: string;
  children?: any;
  onClick?: (ev) => void;
  forwardedRef?: React.MutableRefObject<HTMLSpanElement>;
  size?: 'small' | 'medium';
}

export enum TagColor {
  SUCCESS = 'success',
  WARNING = 'warning',
  ERROR = 'error',
  SECONDARY = 'secondary',
  INFO = 'info',
}

export const Tag: FC<TagProps> = (props) => {
  const { color, children, text, className, onClick, size = 'medium' } = props;

  const styles = useStyles2(getStyles);
  const style: React.CSSProperties = {
    color: text,
  };

  return (
    <span
      style={style}
      className={cx(styles.root, bem(styles.root, size), getMatchingType())}
      onClick={onClick}
      ref={props.forwardedRef}
    >
      {children}
    </span>
  );

  function getMatchingType() {
    return styles[color] ? styles[color] : '';
  }

  function getStyles(theme: GrafanaTheme2) {
    return {
      root: css`
        border-radius: 2px;
        line-height: 100%;
        padding: 5px 8px;
        display: inline-block;
        white-space: nowrap;
        color: ${theme.isDark ? '#fff' : theme.colors.secondary.text};
      `,

      size: css`
        &--small {
          font-size: 12px;
          height: 24px;
        }
      `,

      success: css`
        background-color: ${theme.colors.success.main};
        border: solid 1px ${theme.colors.success.main};
      `,
      warning: css`
        background-color: ${theme.colors.warning.main};
        border: solid 1px ${theme.colors.warning.main};
      `,
      error: css`
        background-color: ${theme.colors.error.main};
        border: solid 1px ${theme.colors.error.main};
      `,
      secondary: css`
        background-color: ${theme.colors.secondary.main};
        border: solid 1px ${theme.colors.secondary.main};
      `,
      info: css`
        background-color: ${theme.colors.primary.main};
        border: solid 1px ${theme.colors.primary.main};
      `,
    };
  }
};
