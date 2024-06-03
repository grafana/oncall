import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getCommonServiceNowConfigStyles = (theme: GrafanaTheme2) => {
  return {
    border: css`
      padding: 12px;
      margin-bottom: 24px;
      border: 1px solid ${theme.colors.border.weak};
      border-radius: 2px;
    `,

    tokenContainer: css`
      display: flex;
      width: 100%;
      gap: 8px;
    `,

    tokenInput: css`
      height: 32px !important;
    `,

    buttonInputHeight: css`
      input {
        height: 32px !important;
      }
    `,

    tokenIcons: css`
      top: 10px !important;
    `,

    loader: css`
      margin-bottom: 0;
    `,
  };
};
