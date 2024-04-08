import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getUtilStyles = (theme: GrafanaTheme2) => {
  return {
    width100: css`
      width: 100%;
    `,

    thinLineBreak: css`
      width: 100%;
      border-top: 1px solid ${COLORS.ALWAYS_GREY};
      margin-top: 8px;
      opacity: 15%;
    `,

    link: css`
      text-decoration: none !important;
    `,

    cursorDefault: css`
      cursor: default;
    `,
  };
};

export enum COLORS {
  ALWAYS_GREY = '#ccccdc',
  GRAY_8 = '#595959',
  GREEN_5 = '#6ccf8e',
}
