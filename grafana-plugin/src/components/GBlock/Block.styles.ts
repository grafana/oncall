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
        background: ${theme.isLight ? '#f4f5f5' : 'rgba(204, 204, 220, 0.12)'};
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
