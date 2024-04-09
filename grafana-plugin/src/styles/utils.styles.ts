import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getUtilStyles = (_theme: GrafanaTheme2) => {
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

export const bem = (...args: string[]) =>
  args.reduce((out, x, i) => {
    out += x;
    if (i === args.length - 1) {
      return out;
    } else if (i === 0) {
      return (out += '--');
    }

    return (out += '-');
  }, '');


export enum COLORS {
  ALWAYS_GREY = '#ccccdc',
  GRAY_8 = '#595959',
  GREEN_5 = '#6ccf8e',
}
