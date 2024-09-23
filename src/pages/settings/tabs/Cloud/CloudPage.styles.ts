import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getCloudPageStyles = (theme: GrafanaTheme2) => {
  return {
    infoBlock: css`
      width: 70%;
      min-width: 1100px;
      padding: 24px;
    `,

    warningMessage: css`
      color: ${theme.colors.warning.text};
    `,

    successMessage: css`
      color: ${theme.colors.success.text};
    `,

    errorMessage: css`
      color: ${theme.colors.error.text};
    `,

    userTable: css`
      margin-top: 24px;
      width: 100%;
    `,

    userRow: css`
      height: 32px;
    `,

    heartbeatButton: css`
      margin-top: 24px;
    `,

    cloudOncallName: css`
      color: #f55f3e;
    `,

    blockIcon: css`
      color: ${theme.colors.secondary.text};
    `,

    errorIcon: css`
      display: inline-block;
      white-space: break-spaces;
      line-height: 20px;
      color: ${theme.colors.error.text} svg {
        vertical-align: middle;
      }
    `,

    heartIcon: css`
      color: ${theme.colors.secondary.text};
      margin-right: 8px;
    `,

    blockButton: css`
      margin-top: 24px;
    `,

    tableTitle: css`
      margin-bottom: 16px;
    `,

    tableButton: css`
      float: right;
    `,
  };
};
