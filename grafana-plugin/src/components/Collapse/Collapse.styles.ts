import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getCollapseStyles = (theme: GrafanaTheme2) => {
  return {
    root: css`
      border: 1px solid ${theme.colors.border.weak};
      width: 100%;
    `,

    header: css`
      padding: 8px;
      cursor: pointer;
      display: flex;
      align-items: center;
    `,

    headerWithBackground: css`
      background: ${theme.colors.secondary.main};
    `,

    label: css`
      display: block;
      margin-left: 8px;
      flex-grow: 1;
    `,

    content: css`
      padding: 16px;
    `,

    icon: css`
      color: ${theme.colors.secondary.text};
      transform-origin: center;
      transition: transform 0.2s;

      &--rotated {
        transform: rotate(90deg);
      }
    `,
  };
};
