import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getCardButtonStyles = (theme: GrafanaTheme2) => {
  return {
    root: css`
      height: 88px;
      position: relative;
      cursor: pointer;
    `,

    icon: css`
      position: absolute;
      left: 20px;
      top: 20px;
      color: ${theme.colors.text.disabled};
    `,

    meta: css`
      position: absolute;
      top: 14px;
      left: 90px;
    `,

    rootSelected: css`
      &::before {
        display: block;
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 4px;
        background-image: ${theme.colors.gradients.brandVertical};
      }
    `,
  };
};
