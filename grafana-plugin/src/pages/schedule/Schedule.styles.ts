import { css } from '@emotion/css';

export const getScheduleStyles = () => {
  return {
    title: css`
      display: flex;
      flex-wrap: wrap;
      flex-direction: row;
      column-gap: 8px;
      row-gap: 8px;
      min-width: 250px;
      align-items: center;
    `,

    header: css`
      position: sticky;
      width: 100%;
    `,

    desc: css`
      width: 736px;
    `,

    usersTimezone: css`
      width: 100%;
    `,

    controls: css`
      width: 100%;
    `,

    rotations: css`
      display: flex;
      flex-direction: column;
      gap: 16px;
      position: relative;
      width: 100%;
    `,

    notFound: css`
      margin: 50px auto;
      text-align: center;
    `,
  };
};
