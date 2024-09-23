import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getAddRespondersPopupStyles = (theme: GrafanaTheme2) => {
  return {
    addRespondersDropdown: css`
      max-height: 500px;
      overflow: hidden;
      border: 1px solid ${theme.colors.border.medium};
      position: absolute;
      right: 16px;
      top: 55px;
      background: ${theme.colors.background.primary};
      width: 340px;
      z-index: 10;
    `,

    infoAlert: css`
      margin: 8px;
    `,

    learnMoreLink: css`
      display: inline-block;
    `,

    responderItem: css`
      cursor: pointer;
      width: 280px;
      overflow: hidden;
    `,

    responderName: css`
      word-break: normal;
    `,

    responderTeam: css`
      text-align: right;
    `,

    respondersFilters: css`
      margin: 8px;
    `,

    radioButtons: css`
      margin: 8px;
    `,

    LoadingPlaceholder: css`
      margin: 8px;
    `,

    table: css`
      max-height: 150px;
      overflow: auto;
      padding: 4px 0;

      & tr:hover {
        background: ${theme.colors.background.secondary} !important;
      }

      & tbody tr:nth-child(odd) {
        background: unset;
      }
    `,

    userResultsSectionHeader: css`
      padding: 10px 8px;
    `,
  };
};
