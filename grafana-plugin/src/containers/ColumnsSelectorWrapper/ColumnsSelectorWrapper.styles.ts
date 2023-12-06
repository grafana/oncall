import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getColumnsSelectorWrapperStyles = (theme: GrafanaTheme2) => {
  return {
    input: css`
      margin-bottom: 16px;
    `,
    fieldRow: css`
      width: 100%;
      display: flex;
      flex-direction: row;
      align-items: 'center';
      gap: 16px;
      padding: 7px;
    `,
    content: css`
      width: 100%;
      min-height: 100px;
    `,
    removalModal: css`
      max-width: 500px;
    `,
    totalValuesCount: css`
      margin-left: 16px;
    `,
    valuesBlock: css`
      margin-bottom: 12px;
    `,
    floatingContainer: css`
      position: relative;
    `,
    floatingContent: css`
      position: absolute;
      top: 40px;
      right: 0;
      display: none;
      background-color: ${theme.colors.background.secondary};
      padding: 16px;
      z-index: 101;
      overflow: hidden;
    `,
    floatingContentVisible: css`
      display: block;
    `,
    checkboxAddOption: css`
      top: 3px;
    `,
  };
};
