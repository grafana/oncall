import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getBlockStyles = (theme: GrafanaTheme2) => {
  return {
    root: css`
      padding: 16px;
      border-radius: 2px;

      &--withBackGround {
        background: ${theme.colors.background.secondary};
      }

      &--fullWidth {
        width: 100%;
      }

      &--hover:hover {
        background: var(--hover-selected);
      }

      &--bordered {
        border: 1px solid ${theme.colors.border.weak};
      }

      &--shadowed {
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.6);
      }
    `,
  };
};
