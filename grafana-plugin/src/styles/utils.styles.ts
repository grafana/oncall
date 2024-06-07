import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import tinycolor from 'tinycolor2';

export const getUtilStyles = (theme: GrafanaTheme2) => {
  return {
    width100: css`
      width: 100%;
    `,

    loadingPlaceholder: css`
      margin-bottom: 0;
      margin-right: 4px;
    `,

    disabled: css`
      opacity: 0.5;
    `,

    thinLineBreak: css`
      width: 100%;
      border-top: 1px solid ${theme.colors.secondary.contrastText};
      margin-top: 8px;
      opacity: 15%;
    `,

    link: css`
      text-decoration: none !important;
    `,

    cursorDefault: css`
      cursor: default;
    `,

    wordBreakAll: css`
      word-break: break-all;
    `,

    ...getCommonFlexStyles(),
    ...getCommonOverflowStyles(),
  };
};

const getCommonOverflowStyles = () => {
  return {
    overflowChild: css`
      overflow: hidden;
      text-overflow: ellipsis;
      display: -webkit-box;
      white-space: initial;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;

      ${[1, 2, 3].map(
        (num) => `
        &--line-${num} {
          -webkit-line-clamp: ${num} !important;
        }
      `
      )}
    `,
  };
};

const getCommonFlexStyles = () => {
  return {
    flex: css`
      display: flex;
      flex-direction: row;
    `,

    // TODO: auto-generate these incrementally instead (XS, MD, LG etc, simillar to overflow)
    flexGapXS: css`
      gap: 4px;
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
  BORDER = 'rgba(204, 204, 220, 0.25)',
}
