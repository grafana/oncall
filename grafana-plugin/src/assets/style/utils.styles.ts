import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getUtilStyles = (theme: GrafanaTheme2) => {
  return {
    width100: css`
      width: 100%;
    `,

    filterTable: css`
      white-space: break-spaces;
      line-height: 20px;
      height: auto;
    `,
  };
};

export enum COLORS {
  ALWAYS_GREY = '#ccccdc',
}
