import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getEscalationChainStyles = (theme: GrafanaTheme2) => {
  return {
    filters: css`
      margin-bottom: 20px;
    `,

    loading: css`
      margin: 10px 20px;
    `,

    escalations: css`
      width: 100%;
      display: flex;
      align-items: flex-start;
      border: 1px solid ${theme.colors.border.weak};
      border-radius: 2px;
    `,

    newEscalationChain: css`
      margin: 16px;
      width: calc(100% - 32px);
    `,

    leftColumn: css`
      width: 300px;
      flex-shrink: 0;
      border-right: 1px solid ${theme.colors.border.weak};
    `,

    escalationsList: css`
      overflow: auto;
      max-height: 70vh;
    `,

    escalation: css`
      margin: 16px;
      flex-grow: 1;
      display: flex;
      gap: 10px;
      flex-direction: column;
    `,

    header: css`
      display: flex;
      justify-content: space-between;
      align-items: center;
    `,

    list: css`
      margin: 0;
      list-style-type: none;
    `,

    buttons: css`
      padding-bottom: 24px;
    `,
  };
};
