import { css } from '@emotion/css';

export const getApiTokenFormStyles = () => {
  return {
    tokenInputContainer: css`
      width: 100%;
      display: flex;
    `,
    tokenInput: css`
      border-top-right-radius: 0;
      border-bottom-right-radius: 0;
    `,
    tokenCopyButton: css`
      border-top-left-radius: 0;
      border-bottom-left-radius: 0;
    `,
    field: css`
      flex-grow: 1;
    `,
  };
};
