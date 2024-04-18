import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getStyles = (_theme: GrafanaTheme2) => ({
  formRow: css`
    display: flex;
    flex-wrap: nowrap;
    gap: 4px;
  `,
  formField: css`
    flex-grow: 1;
  `,
});
