import React, { FC } from 'react';

import { css, cx } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { useStyles2 } from '@grafana/ui';
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

  SUCCESS_LABEL = 'successLabel',
  WARNING_LABEL = 'warningLabel',
  ERROR_LABEL = 'errorLabel',
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
      className={cx(styles.root, bem(styles.root, size), getMatchingClass(), className)}
      onClick={onClick}
      ref={props.forwardedRef}
    >
      {children}
    </span>
  );

  function getMatchingClass() {
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
        color: ${theme.isDark ? '#fff' : theme.colors.success.contrastText};
      `,
      warning: css`
        background-color: ${theme.colors.warning.main};
        border: solid 1px ${theme.colors.warning.main};
        color: #fff;
      `,
      error: css`
        background-color: ${theme.colors.error.main};
        border: solid 1px ${theme.colors.error.main};
        color: ${theme.isDark ? '#fff' : theme.colors.error.contrastText};
      `,
      secondary: css`
        background-color: ${theme.colors.secondary.main};
        border: solid 1px ${theme.colors.secondary.main};
        color: ${theme.isDark ? '#fff' : theme.colors.secondary.contrastText};
      `,
      info: css`
        background-color: ${theme.colors.primary.main};
        border: solid 1px ${theme.colors.primary.main};
        color: ${theme.isDark ? '#fff' : theme.colors.info.contrastText};
      `,

      successLabel: getLabelCss('green', theme),
      warningLabel: getLabelCss('orange', theme),
      errorLabel: getLabelCss('red', theme),
    };
  }

  function getLabelCss(color: string, theme: GrafanaTheme2) {
    let sourceColor = theme.visualization.getColorByName(color);
    let bgColor = '';
    let textColor = '';
  
    if (theme.isDark) {
      bgColor = tinycolor(sourceColor).setAlpha(0.25).toString();
      textColor = tinycolor(sourceColor).lighten(15).toString();
    } else {
      bgColor = tinycolor(sourceColor).setAlpha(0.25).toString();
      textColor = tinycolor(sourceColor).darken(20).toString();
    }

    return css`
      border: 1px solid ${sourceColor};
      background-color: ${bgColor};
      color: ${textColor};
    `
  }
};
