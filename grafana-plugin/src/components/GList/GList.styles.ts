import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getGListStyles = (theme: GrafanaTheme2) => {
  return {
    root: css`
      width: 100%;
      display: flex;
      flex-direction: column;
    `,

    item: css`
      padding: 16px;
      width: 100%;
      border: 1px solid ${theme.colors.border.weak};
      position: relative;
      cursor: pointer;

      &:first-child {
        border-top: 1px solid ${theme.colors.border.weak};
      }

      &:hover {
        background: ${theme.colors.background.secondary};
      }
    `,

    item_selected: css`
      cursor: default;
      background: ${theme.colors.background.secondary};

      &::before {
        display: block;
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 4px;
        background-image: linear-gradient(270deg, #f55f3e 0%, #f83 100%);
      }
    `,
  };
};
