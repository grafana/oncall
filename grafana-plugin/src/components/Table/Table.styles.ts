import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getTableStyles = (theme: GrafanaTheme2) => {
  return {
    root: css`
      width: 100%;

      table {
        width: 100%;
      }

      tr {
        min-height: 56px;
      }

      th:first-child {
        padding-left: 20px;
      }

      td {
        min-height: 60px;
        padding-top: 10px;
        padding-bottom: 10px;
      }
    `,

    pagination: css`
      width: 100%;
      margin-top: 20px;
    `,

    expandIcon: css`
      padding: 10px;
      color: ${theme.colors.text.primary};
      pointer-events: none;
      transform: rotate(-90deg);
      transform-origin: center;
      transition: transform 0.2s;

      &--expanded {
        transform: rotate(0deg) translateY(-5px); // to manually compensate for top: 3px
      }
    `,

    rowEven: css`
      background: ${theme.colors.background.secondary};
    `,
  };
};
