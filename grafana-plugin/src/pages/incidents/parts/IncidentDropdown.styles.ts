import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getIncidentDropdownStyles = (theme: GrafanaTheme2) => {
  return {
    incidentTag: css`
      padding: 5px 8px;
      display: inline-flex;
      align-items: center;
      cursor: pointer;
    `,

    incidentIcon: css`
      margin-right: -4px;
      margin-left: 2px;
    `,

    incidentOptions: css`
      display: flex;
      flex-direction: column;
    `,

    incidentOptionItem: css`
      padding: 8px;
      display: flex;
      align-items: center;
      flex-direction: row;
      flex-shrink: 0;
      white-space: nowrap;
      border-left: 2px solid transparent;
      cursor: pointer;
      min-width: 84px;
      display: flex;
      gap: 8px;
      flex-direction: row;
      color: ${theme.colors.text.primary};

      &:hover {
        background: ${theme.colors.action.hover};
      }
    `,

    incidentOptionEl: css`
      > div {
        margin: 0;
      }
    `,
  };
};
