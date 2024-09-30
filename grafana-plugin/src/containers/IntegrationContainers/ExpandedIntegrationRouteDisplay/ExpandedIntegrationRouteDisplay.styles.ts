import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { Colors } from 'styles/utils.styles';

export const getExpandedIntegrationRouteDisplayStyles = (theme: GrafanaTheme2) => {
  return {
    input: css`
      border: 1px solid ${theme.colors.border.weak};
    `,

    inputAlign: css`
      width: 728px;
    `,

    fields: css`
      margin-bottom: 0;
    `,

    routingAlert: css`
      width: 765px;
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
        background: ${theme.isLight ? Colors.HOVER : Colors.GRAY_9};
      }
    `,

    routingTemplateContainer: css`
      margin-bottom: 8px;
    `,

    adjustElementPadding: css`
      padding-top: 6px;
    `,

    defaultRouteView: css`
      min-height: 40px;
    `,

    block: css`
      width: 100%;
      background-color: ${theme.colors.background.secondary};
      border: 1px solid ${theme.colors.border.medium} !important;
    `,

    labelsPanel: css`
      display: flex;
      width: 100%;
      justify-content: space-between;
    `,

    headingContainer: css`
      width: 100%;
      display: flex;
      flex-direction: row;
      flex-wrap: nowrap;
      overflow: hidden;
      gap: 12px;
    `,

    headingContainerItem: css`
      display: flex;
      white-space: nowrap;
      flex-direction: row;
      gap: 8px;
    `,

    headingContainerItemLarge: css`
      flex-grow: 1;
      overflow: hidden;
    `,

    headingContainerItemText: css`
      overflow: hidden;
      max-width: calc(100% - 48px);
      text-overflow: ellipsis;
    `,
  };
};
