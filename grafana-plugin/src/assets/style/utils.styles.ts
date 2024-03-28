import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getUtilStyles = (theme: GrafanaTheme2) => {
  return {
    width100: css`
      width: 100%;
    `,
  };
};
