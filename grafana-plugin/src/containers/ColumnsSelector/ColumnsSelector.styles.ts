import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getColumnsSelectorStyles = (_theme: GrafanaTheme2) => {
  return {
    columnsSelectorView: css`
      min-width: 230px;
    `,

    columnsVisibleSection: css`
      margin-bottom: 16px;
      max-height: 250px;
      overflow-y: scroll;
      overflow-x: hidden;
    `,

    columnsHeader: css`
      display: block !important;
      margin-bottom: 16px;
    `,
    columnsHeaderSmall: css`
      display: block !important;
      margin-bottom: 8px;
    `,

    columnsHeaderSecondary: css`
      display: block;
      margin-bottom: 8px;
    `,

    columnsHiddenSection: css`
      margin-bottom: 20px;
      max-height: 250px;
      overflow-y: auto;
    `,
    columnsSelectorButtons: css`
      display: flex;
      justify-content: flex-end;
      gap: 8px;
      width: 100%;
    `,

    columnItem: css`
      gap: 12px;
      display: flex;
      padding-left: 25px;
      align-items: center;

      &:hover .columns-icon-trash {
        display: block;
      }
    `,

    columnsCheckbox: css`
      position: absolute;
      top: 2px;
      left: 0;
    `,

    columnsIcon: css`
      display: block;
      margin-left: auto;
      position: relative;
      top: -2px;

      &::before {
        top: 50%;
        left: 50%;
        border-radius: 50%;
        transform: translate(-50%, -60%);
      }
    `,

    columnsIconTrash: css`
      display: none;
    `,

    columnRow: css`
      position: relative;
      margin-bottom: 6px;
      height: 22px;
    `,

    columnName: css`
      text-wrap: nowrap;
      max-width: 180px;
      text-overflow: ellipsis;
      display: block;
      overflow: hidden;
    `,

    labelIcon: css`
      margin: 0;
      padding: 0;
    `,
  };
};
