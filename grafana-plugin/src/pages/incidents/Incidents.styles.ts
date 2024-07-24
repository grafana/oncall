import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getIncidentsStyles = (theme: GrafanaTheme2) => {
  return {
    select: css`
      width: 400px;
    `,

    rightSideFilters: css`
      display: flex;
      gap: 8px;
    `,

    alertsSelected: css`
      white-space: nowrap;
    `,

    actionButtons: css`
      width: 100%;
      justify-content: flex-end;
    `,

    filters: css`
      margin-bottom: 20px;
    `,

    fieldsDropdown: css`
      gap: 8px;
      display: flex;
      margin-left: auto;
      align-items: center;
      padding-left: 4px;
    `,

    aboveIncidentsTable: css`
      display: flex;
      justify-content: space-between;
      align-items: center;
    `,

    horizontalScrollTable: css`
      table td:global(.rc-table-cell) {
        white-space: nowrap;
        padding-right: 16px;
      }
    `,

    bulkActionsContainer: css`
      margin: 10px 0 10px 0;
      display: flex;
      width: 100%;
    `,

    bulkActionsList: css`
      display: flex;
      align-items: center;
      gap: 8px;
    `,

    otherUsers: css`
      color: ${theme.colors.secondary.text};
    `,

    pagination: css`
      width: 100%;
      margin-top: 20px;
    `,

    title: css`
      margin-bottom: 24px;
      right: 0;
    `,

    btnResults: css`
      margin-left: 8px;
    `,

    /* filter cards */

    cards: css`
      margin-top: 25px;
    `,

    row: css`
      display: flex;
      flex-wrap: wrap;
      margin-left: -8px;
      margin-right: -8px;
      row-gap: 16px;
    `,

    loadingPlaceholder: css`
      margin-bottom: 0;
      text-align: center;
    `,

    col: css`
      padding-left: 8px;
      padding-right: 8px;
      display: block;
      flex: 0 0 25%;
      max-width: 25%;

      @media (max-width: 1200px) {
        flex: 0 0 50%;
        max-width: 50%;
      }

      @media (max-width: 800px) {
        flex: 0 0 100%;
        max-width: 100%;
      }
    `,
  };
};
