import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import tinycolor from 'tinycolor2';

export const getUtilStyles = (theme: GrafanaTheme2) => {
  return {
    width100: css`
      width: 100%;
    `,

    disabled: css`
      opacity: 0.5;
    `,

    thinLineBreak: css`
      width: 100%;
      border-top: 1px solid ${theme.colors.secondary.main};
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

export function getLabelBackgroundTextColorObject(
  color: string,
  theme: GrafanaTheme2
): { bgColor: string; textColor: string; sourceColor: string } {
  let sourceColor = theme.visualization.getColorByName(color);
  let bgColor = '';
  let textColor = '';

  if (theme.isDark) {
    bgColor = tinycolor(sourceColor).setAlpha(0.25).toString();
    textColor = tinycolor(sourceColor).lighten(15).toString();
  } else {
    bgColor = tinycolor(sourceColor).setAlpha(0.25).toString();
    textColor = tinycolor(sourceColor).darken(20).toString();
  }

  return { bgColor, textColor, sourceColor };
}

export function getLabelCss(color: string, theme: GrafanaTheme2) {
  const { bgColor, textColor, sourceColor } = getLabelBackgroundTextColorObject(color, theme);
  return css`
    border: 1px solid ${sourceColor};
    background-color: ${bgColor};
    color: ${textColor};
  `;
}

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
  GRAY_9 = '#434343',
  GREEN_5 = '#6ccf8e',
}
