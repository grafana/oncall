import { css } from '@emotion/css';

export const getSchedulesStyles = () => {
  return {
    schedule: css`
      position: relative;
    `,

    table: css`
      td {
        padding-top: 5px;
        padding-bottom: 5px;
      }
    `,

    schedulePersonal: css`
      position: relative;
      margin: 20px 0;
    `,

    title: css`
      margin-bottom: 16px;
    `,

    buttons: css`
      padding-right: 10px;
    `,

    rotations: css`
      position: relative;
    `,

    schedulesFiltersContainer: css`
      display: flex;
      flex-direction: row;
      flex-wrap: wrap;
      row-gap: 4px;
      column-gap: 8px;
      width: 100%;
      margin-bottom: 20px;
    `,

    schedulesActions: css`
      display: flex;
      justify-content: flex-end;
      flex-grow: 1;
      gap: 8px;
    `,
  };
};
