import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getCheatSheetStyles = (theme: GrafanaTheme2) => {
  return {
    cheatsheetContainer: css`
      width: 40%;
      height: 100%;
      padding: 16px;
      padding-right: 0;
      border: 1px solid ${theme.colors.border.weak};
      min-width: min-content;
      overflow-y: scroll;
    `,

    cheatsheetInnerContainer: css`
      padding-right: 16px;
      overflow-y: scroll;
      height: 100%;
    
      & > div {
        height: 100%;
        max-height: 100%;
      }
    }`,

    cheatsheetItem: css`
      margin-bottom: 24px;

      &--small {
        margin-bottom: 16px;
        width: 100%;
      }
    `,

    code: css`
      white-space: pre;
    `,
  };
};
