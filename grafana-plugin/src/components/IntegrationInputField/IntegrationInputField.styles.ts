import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getIntegrationInputFieldStyles = (_theme: GrafanaTheme2) => {
  return {
    root: css`
      position: relative;
      display: flex;
      flex-grow: 1;
      height: 25px;
    `,

    icons: css`
      position: absolute;
      right: 8px;
      top: 6px;
      z-index: 10;
    `,

    inputContainer: css`
      width: 100%;

      input {
        height: 25px;
        padding-right: 78px;
        text-overflow: ellipsis;
      }
    `,

    buttonInputHeight: css`
      input {
        height: 32px;
      }
    `,
  };
};
