import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { COLORS } from 'styles/utils.styles';

export const getIntegrationsStyles = (theme: GrafanaTheme2) => {
  return {
    newIntegrationButton: css`
      width: 180px;
    `,

    heartbeatBadge: css`
      padding: 4px 10px;
      width: 40px;
    `,

    title: css`
      margin-bottom: 16px;
    `,

    tabsBar: css`
      margin-bottom: 24px;
    `,

    integrationsHeader: css`
      margin-bottom: 24px;
      right: 0;
    `,

    integrationsTableRow: css`
      height: 40px;
    `,

    integrationsTable: css`
      margin-top: 16px;
    `,

    integrationsActionsList: css`
      display: flex;
      flex-direction: column;
      width: 200px;
      border-radius: 2px;
    `,

    integrationsActionItem: css`
      padding: 8px;
      display: flex;
      align-items: center;
      flex-direction: row;
      flex-shrink: 0;
      white-space: nowrap;
      border-left: 2px solid transparent;
      cursor: pointer;
      min-width: 84px;
      display: flex;
      gap: 8px;
      flex-direction: row;

      &:hover {
        background: ${theme.isLight ? 'rgba(244, 245, 245)' : COLORS.GRAY_9};
      }
    `,

    goToDirectPagingAlert: css`
      margin-top: 24px;
    `,

    buttons: css`
      padding-bottom: 24px;
    `,
  };
};
