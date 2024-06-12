import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getUsersStyles = (theme: GrafanaTheme2) => {
  return {
    usersTtitle: css`
      display: flex;
      align-items: center;
      justify-content: center;
    `,

    userAvatar: css`
      margin-right: 10px;
    `,

    usersFilters: css`
      margin-bottom: 20px;
    `,

    usersHeader: css`
      display: flex;
      justify-content: space-between;
      margin-bottom: 16px;
    `,

    usersHeaderLeft: css`
      display: flex;
      align-items: baseline;
    `,

    usersTitle: css`
      margin-bottom: 0;
    `,

    usersFooter: css`
      display: flex;
      justify-content: flex-end;
    `,

    desc: css`
      word-wrap: break-word;
      word-break: break-word;
    `,

    userFiltersContainer: css`
      display: flex;
      justify-content: space-between;
    `,

    warningMessageIcon: css`
      margin-right: 8px;
      color: ${theme.colors.warning.text};
    `,

    errorIcon: css`
      display: inline-block;
      white-space: break-spaces;
      line-height: 20px;
      color: ${theme.colors.error.text};

      svg {
        vertical-align: middle;
      }
    `,

    warningMessage: css`
      color: ${theme.colors.warning.text};
    `,

    successMessage: css`
      color: ${theme.colors.success.text};
    `,
  };
};
