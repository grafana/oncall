import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getTooltipBadgeStyles = (theme: GrafanaTheme2) => {
  return {
    element: css`
      font-size: 12px;
      line-height: 16px;
      padding: 3px 4px;
      border-radius: 2px;
      display: inline-block;

      &--primary {
        background: var(--tag-background-primary);
        border: 1px solid var(--tag-border-primary);
        color: var(--tag-text-primary);
      }

      &--secondary {
        background: var(--background-secondary);
        border: var(--border);
        color: var(--primary-text-color);
      }

      &--warning {
        background: var(--tag-background-warning);
        border: 1px solid var(--tag-border-warning);
        color: var(--tag-text-warning);
      }

      &--success {
        background: var(--tag-background-success);
        border: 1px solid var(--tag-border-success);
        color: var(--tag-text-success);
      }

      &--danger {
        background: var(--tag-background-danger);
        border: 1px solid var(--tag-border-danger);
        color: var(--tag-text-danger);
      }

      &--padding {
        padding: 3px 10px;
      }
    `,

    tooltip: css`
      width: auto;
    `,
  };
};
