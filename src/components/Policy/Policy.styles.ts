import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getPolicyStyles = (_theme: GrafanaTheme2) => {
  return {
    note: css`
      white-space: nowrap;
    `,

    noteIcon: css`
      padding-right: 6px;

      &--green {
        color: green;
      }

      &--orange {
        color: orange;
      }

      &--default {
        color: #1890ff;
      }
    `,

    tooltip: css`
      max-width: none !important;
    `,

    control: css`
      margin-right: 10px !important;
    `,

    handle: css`
      cursor: move;

      &--disabled {
        cursor: not-allowed;
        pointer-events: none;
      }
    `,
  };
};
