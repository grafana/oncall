import { css } from '@emotion/css';

export const getTimelineStyles = () => {
  return {
    root: css`
      padding: 0;
      margin: 0;
      list-style: none;
    `,

    item: css`
      display: flex;
      align-items: center;
      margin: 10px 0;
    `,

    dot: css`
      width: 28px;
      height: 28px;
      border-radius: 50%;
      text-align: center;
      line-height: 28px;
      font-size: 14px;
      font-weight: 400;
      color: white;
      flex-shrink: 0;
    `,

    content: css`
      margin: 0 0 0 24px;
      word-break: break-word;
      flex-grow: 1;
    `,

    contentNoMargin: css`
      margin: 0;
    `,
  };
};
