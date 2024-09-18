import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { Colors } from 'styles/utils.styles';

export const getUserGroupStyles = (theme: GrafanaTheme2) => {
  return {
    root: css`
      width: 100%;
    `,

    sortable: css`
      z-index: 1062;
      box-shadow: ${theme.isDark ? 'rgb(17 18 23) 0 0 0 2px, rgb(61 113 217) 0 0 0 4px;' : ''};
      background: ${theme.isDark ? '#34363d' : ''};
    `,

    separator: css`
      font-weight: 400;
      font-size: 12px;
      line-height: 16px;
      text-align: center;
      margin: 4px 0;
      display: flex;
      align-items: center;
      justify-content: center;

      &__clickable {
        cursor: pointer;
        margin-top: 12px;
      }
    `,

    groups: css`
      width: 100%;
      padding: 0;
      margin: 0;
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 1px;
    `,

    user: css`
      background: #${theme.colors.background.secondary};
      border-radius: 2px;
      display: flex;
      position: relative;

      &:hover {
        background: ${theme.colors.action.hover};
      }
    `,

    userButtons: css`
      position: absolute;
      top: 8px;
      right: 5px;
    `,

    icon: css`
      display: block;
      color: ${Colors.ALWAYS_GREY};

      &:hover {
        color: #fff;
      }
    `,

    addUserGroup: css`
      width: 100%;
      text-align: center;
      font-weight: 400;
      font-size: 12px;
      line-height: 16px;
      color: ${theme.colors.text.secondary};
      cursor: pointer;
    `,

    select: css`
      width: 100%;
    `,
  };
};
