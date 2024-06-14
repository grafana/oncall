import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { getLabelCss } from 'styles/utils.styles';

export const getTooltipBadgeStyles = (theme: GrafanaTheme2) => {
  return {
    primary: getLabelCss('blue', theme),
    warning: getLabelCss('orange', theme),
    success: getLabelCss('green', theme),
    danger: getLabelCss('red', theme),

    secondary: css`
      background: ${theme.colors.background.secondary};
      border: 1px solid ${theme.colors.border.weak};
      color: ${theme.colors.text.primary};
    `,

    element: css`
      font-size: 12px;
      line-height: 16px;
      padding: 3px 4px;
      border-radius: 2px;
      display: inline-block;

      &--padding {
        padding: 3px 10px;
      }
    `,

    tooltip: css`
      width: auto;
    `,
  };
};
