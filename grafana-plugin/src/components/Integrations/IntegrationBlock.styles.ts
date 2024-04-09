import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getIntegrationBlockStyles = (theme: GrafanaTheme2) => {
  return {
    integrationBlockHeading: css`
      padding: 16px;
      background-color: ${theme.colors.background.secondary};
      border: 1px solid ${theme.components.panel.borderColor} !important;
      border-radius: 4px;

      &--noBorderBottom {
        border-bottom-left-radius: 0 !important;
        border-bottom-right-radius: 0 !important;
      }
    `,

    integrationBlockContent: css`
      padding: 15px;
      background: ${theme.colors.background.primary};
      border: 1px solid ${theme.components.panel.borderColor} !important;
      border-top: none !important;
      border-bottom-left-radius: 4px !important;
      border-bottom-right-radius: 4px !important;
    `,
  };
};
