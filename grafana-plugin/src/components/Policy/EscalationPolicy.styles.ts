import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getEscalationPolicyStyles = (theme: GrafanaTheme2) => {
  return {
    root: css`
      display: flex;
      justify-content: flex-start;
      align-items: center;
      border-radius: 2px;
      background: ${theme.colors.background.secondary};
      padding: 2px 2px 2px 12px;
      flex-wrap: wrap;
      min-height: 36px;
    `,

    step: css`
      & > * {
        margin-right: 8px !important;
      }
    `,

    select: css`
      flex-shrink: 0;
      min-width: 100px;
    `,

    multiSelect: css`
      max-width: 90%;
      padding: 4px;
    `,

    users: css`
      flex-grow: 1;
      width: 400px;
    `,

    timeline: css`
      width: 400px;
    `,

    control: css`
      margin: 0 8px;
      width: auto !important;
    `,

    delete: css`
      margin-left: auto !important;
    `,
  };
};
