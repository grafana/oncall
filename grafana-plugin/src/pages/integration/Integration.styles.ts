import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { Colors } from 'styles/utils.styles';

export const getIntegrationStyles = (theme: GrafanaTheme2) => {
  return {
    backArrow: css`
      padding-top: 8px;
    `,
    contactPointsWarning: css`
      padding-top: 12px;
    `,
    contactPointContainer: css`
      display: flex;
      flex-direction: row;
      gap: 8px;
    `,
    integrationActionItem: css`
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

      &:hover {
        background: ${theme.isDark ? Colors.GRAY_9 : Colors.HOVER};
      }
    `,
    integrationDescriptionAlert: css`
      padding-top: 24px;

      a {
        color: ${theme.colors.info.text};
      }
    `,
    customiseButton: css`
      button {
        padding: 15px;
      }
    `,
    input: css`
      flex-grow: 1;
      max-width: calc(100% - 80px);

      ${theme.isLight ? `border: 1px solid ${theme.colors.border.weak}` : ``}
    `,
    inputWithToggler: css`
      max-width: calc(100% - 134px);
    `,
    routesSectionHeading: css`
      font-size: 16px;
    `,
    howToConnectContainer: css`
      display: flex;
      align-items: center;
      gap: 8px;
    `,
    heartbeatBadge: css`
      padding: 4px 8px;
    `,
    verticalBlock: css`
      display: flex;
      flex-direction: column;
      gap: 8px;
    `,
    templatesContainer: css`
      width: 100%;
      padding-right: 48px;
      display: flex;
      flex-direction: row;
      flex-wrap: nowrap;
      overflow: hidden;
      gap: 12px;
    `,
    templatesItem: css`
      overflow: hidden;
      white-space: nowrap;
      text-overflow: ellipsis;
    `,

    templatesItemLarge: css`
      max-width: calc((100% - 150px) / 2);
    `,
    templatesItemSmall: css`
      max-width: 150px;
    `,
    templatesItemText: css`
      margin-right: 4px;
    `,
    templatesContent: css`
      display: flex;
      width: 100%;
      align-items: center;
      overflow: hidden;
      padding-left: 12px;
    `,
    templatesOuterContainer: css`
      display: flex;
      width: 100%;
      align-items: center;
      overflow: hidden;
    `,

    templatesEdit: css`
      margin-left: 0;
    `,

    templateDrawer: css`
      padding-bottom: 24px;
    `,

    noWrap: css`
      padding-top: 24px;
      white-space: nowrap;
    `,

    headerTop: css`
      display: flex;
      flex-direction: row;
      flex-wrap: wrap;
      width: 100%;
      gap: 8px;
    `,

    headerTopItem: css`
      display: flex;
      flex-direction: row;
      align-items: center;
      gap: 4px;
    `,

    inlineSwitch: css`
      height: 34px;
      border: 1px solid ${theme.colors.border.weak};
    `,

    routeHeading: css`
      max-width: 80%;
      display: block;
      text-overflow: ellipsis;
      overflow: hidden;
    `,

    linkFlex: css`
      align-items: center;
      display: inline-flex;
      gap: 4px;
    `,

    iconExclamation: css`
      color: ${theme.colors.error.text};
    `,

    contactPointsTable: css`
      margin-bottom: 24px;
    `,

    contactPointsConnect: css`
      padding: 12px;
      margin-bottom: 24px;
      border: 1px solid ${theme.colors.border.weak};
      border-radius: 2px;
    `,

    contactPointsConnectToggler: css`
      width: 100%;
    `,

    integrationSubHeadingContainer: css`
      margin-bottom: 24px;
    `,

    integrationPayloadInput: css`
      width: 100%;
    `,

    integrationHeadingContainer: css`
      display: flex;
      gap: 8px;
      align-items: center;
    `,

    integrationHeading: css`
      display: flex;
      justify-content: flex-end;
      flex-direction: row;
      width: 100%;
    `,

    integrationActions: css`
      display: flex;
      gap: 8px;
      margin-left: auto;
    `,

    integrationActionsList: css`
      display: flex;
      flex-direction: column;
      width: 200px;
      border-radius: 2px;
    `,

    integrationDescription: css`
      padding-top: 12px;
      display: block;
    `,

    integrationCounter: css`
      font-size: 12px;
    `,

    integrationCountersBadge: css`
      line-height: 16px;
      padding: 3px 4px;
    `,

    integrationInputField: css`
      margin-right: 24px;
    `,
    integrationName: css`
      margin: 0;
    `,
  };
};
