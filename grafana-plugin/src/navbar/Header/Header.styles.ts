import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getHeaderStyles = (theme: GrafanaTheme2) => {
  return {
    navbarStarIcon: css`
      margin-right: 4px;
    `,

    headerTopNavbar: css`
      padding-top: 0;
      padding-bottom: 0;
      margin-bottom: 32px;
    `,

    navbarHeading: css`
      padding: 4px;
      border: 1px solid ${theme.colors.secondary.border};
      width: initial;
      font-size: 12px;
      padding-top: 0;
      margin-bottom: 0;
    `,

    navbarLink: css`
      display: flex;
      align-items: center;
      padding-top: 6px;
    `,

    navbarLeft: css`
      display: flex;
      flex-basis: 100%;
      align-items: flex-start;
    `,

    navbarHeadingContainer: css`
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      flex-direction: row;
      column-gap: 8px;
      row-gap: 8px;
      margin-left: -50px;
    `,

    irmIcon: css`
      font-size: 12px;
      padding: 2px 4px;
      border: 1px solid #ffb375;
      color: #ffb375;
    `,

    banners: css`
      margin-bottom: 24px;

      &:empty {
        padding-top: 0;
        margin-bottom: 0;
      }
    `,

    logoContainer: css`
      height: 32px;
      margin-top: 2px;
    `,

    pageHeaderImage: css`
      height: 32px;
    `,

    pageHeaderTitle: css`
      margin-bottom: 8px;
    `,
  };
};
