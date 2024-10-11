import { css } from '@emotion/css';

export const getAnimationClasses = () => {
  return {
    enter: css`
      opacity: 0;
    `,
    enterActive: css`
      opacity: 1;
      transition: opacity 500ms ease-in;
    `,
    exit: css`
      opacity: 1;
    `,
    exitActive: css`
      opacity: 0;
      transition: opacity 500ms ease-in;
    `,
  };
};
