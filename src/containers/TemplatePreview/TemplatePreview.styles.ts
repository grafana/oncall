import { css } from '@emotion/css';

export const getTemplatePreviewStyles = () => {
  return {
    img: css`
      width: 100%;
    `,

    message: css`
      word-wrap: break-word;

      ul {
        margin-left: 24px;
      }

      p {
        margin-bottom: 0;
      }

      code {
        white-space: break-spaces;
      }
    `,

    imageResult: css`
      img {
        max-width: 100%;
        max-height: 100%;
      }
    `,

    displayLinebreak: css`
      white-space: pre-line;
    `,

    extraCheck: css`
      margin-bottom: 10px;
    `,
  };
};
