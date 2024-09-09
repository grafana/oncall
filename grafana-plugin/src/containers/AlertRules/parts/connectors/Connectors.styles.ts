import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getConnectorsStyles = (theme: GrafanaTheme2) => {
  return {
    root: css`
      border-radius: 2px;
      background: ${theme.colors.background.secondary};
      padding: 2px 2px 2px 12px;
      flex-wrap: wrap;
      width: 100%;
    `,
  };
};
