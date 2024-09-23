import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

const sharedMaxHeight = css`
  height: 100%;
  max-height: 100%;
`;

const overflowHidden = css`
  overflow-y: hidden;
`;

export const getIntegrationTemplateStyles = (theme: GrafanaTheme2) => {
  return {
    titleContainer: css`
      padding: 24px 24px 0;
    `,
    containerWrapper: css`
      padding: 8px;
      height: 100%;
      max-height: 100%;
    `,
    container: css`
      display: flex;
      height: 100%;
      max-height: 100%;
      width: 100%;
      border: 1px solid ${theme.colors.border.strong};
    `,

    templateBlockTitle: css`
      padding: 16px;
      align-items: baseline;
      height: 56px;
    `,

    templateEditorBlockTitle: css`
        padding: 8px 16px 0;
    align-items: baseline;
    border: 1px solid ${theme.colors.border.weak};
    background-color: ${theme.colors.background.secondary}
    height: 56px;
    min-width: min-content;`,

    templateBlockList: css`
      width: 30%;
      overflow-y: hidden;
      ${sharedMaxHeight}
      ${overflowHidden}
    `,

    templateBlockCodeEditor: css`
      width: 40%;
      overflow-y: hidden;
      ${sharedMaxHeight}
      ${overflowHidden}

      div[aria-label='Code editor container'] {
        border-bottom: none;
      }
    `,

    templateBlockResult: css`
      width: 30%;
      overflow-y: scroll !important;
      padding-right: 16px;
      ${sharedMaxHeight}
    `,

    result: css`
      padding: 0;
      padding-left: 16px;
      padding-bottom: 60px;
      ${sharedMaxHeight}
    `,

    templateEditorBlockContent: css`
      height: calc(100% - 57px);
      border-left: 1px solid ${theme.colors.border.weak};
      border-right: 1px solid ${theme.colors.border.weak};
    `,
  };
};
