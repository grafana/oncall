import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getConnectorsStyles = (theme: GrafanaTheme2) => {
  return {
    root: css`
      border-radius: 2px;
      background: ${theme.colors.background.secondary};
      padding: 2px 2px 2px 12px;
      flex-wrap: wrap;
      width: 100%;
    `,

    userItem: css`
      margin-bottom: 15px;
    `,

    userValue: css`
      font-size: 16px;
    `,

    iCalSettings: css`
      display: block;
    `,

    iCalButton: css`
      margin-top: 24px;
    `,

    icalLinkContainer: css`
      margin-top: 8px;
    `,

    icalLink: css`
      display: block;
      border-radius: 2px;
      border: 1px solid ${theme.colors.border.weak};
      padding: 4px;
      background-color: ${theme.colors.background.secondary};
      overflow-wrap: break-word;
    `,

    warningIcon: css`
      color: ${theme.colors.warning.text};
    `,

    errorMessage: css`
      color: ${theme.colors.error.text};
    `,
  };
};
