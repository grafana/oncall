import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { Colors, getLabelBackgroundTextColorObject } from 'styles/utils.styles';

export const getIncidentStyles = (theme: GrafanaTheme2) => {
  return {
    incidentRow: css`
      display: flex;
    `,

    incidentRowLeftSide: css`
      flex-grow: 1;
    `,

    block: css`
      padding: 0 0 20px 0;
    `,

    payloadSubtitle: css`
      margin-bottom: 16px;
    `,

    infoRow: css`
      width: 100%;
      border-bottom: 1px solid ${theme.colors.border.medium};
      padding-bottom: 20px;
    `,

    buttonsRow: css`
      margin-top: 20px;
    `,

    content: css`
      margin-top: 5px;
      display: flex;
    `,

    timelineIconBackground: css`
      width: 28px;
      height: 28px;
      border-radius: 50%;
      display: flex;
      justify-content: center;
      align-items: center;
      background: rgba(${theme.isDark ? '70, 76, 84, 1' : '70, 76, 84, 0'});
    `,

    message: css`
      margin-top: 16px;
      word-wrap: break-word;

      a {
        word-break: break-all;
        color: ${theme.colors.text.link};
        text-decoration: underline;
      }

      ul {
        margin-left: 24px;
      }

      p {
        margin-bottom: 0;
      }

      code {
        white-space: break-spaces;
      }
    `,

    image: css`
      margin-top: 16px;
      max-width: 100%;
    `,

    collapse: css`
      margin-top: 16px;
      position: relative;
    `,

    column: css`
      width: 50%;
      padding-right: 24px;

      &:not(:first-child) {
        padding-left: 24px;
      }
    `,

    incidentsContent: css`
      > div:not(:last-child) {
        border-bottom: 1px solid ${Colors.BORDER};
        padding-bottom: 16px;
      }

      > div:not(:first-child) {
        padding-top: 16px;
      }
    `,

    timeline: css`
      list-style-type: none;
      margin: 0 0 24px 12px;
    `,

    timelineItem: css`
      margin-top: 12px;
    `,

    notFound: css`
      margin: 50px auto;
      text-align: center;
    `,

    alertGroupStub: css`
      margin: 24px auto;
      width: 520px;
      text-align: center;
    `,

    alertGroupStubDivider: css`
      width: 520px;
    `,

    blue: css`
      background: ${getLabelBackgroundTextColorObject('blue', theme).sourceColor};
    `,

    timelineTitle: css`
      margin-bottom: 24px;
    `,

    timelineFilter: css`
      margin-bottom: 24px;
    `,

    titleIcon: css`
      color: ${theme.colors.secondary.text};
      margin-left: 4px;
    `,

    integrationLogo: css`
      margin-right: 8px;
    `,

    labelButton: css`
      padding: 0 8px;
      font-weight: 400;

      &:disabled {
        border: 1px solid ${theme.colors.border.strong};
      }
    `,

    labelButtonText: css`
      max-width: 160px;
      overflow: hidden;
      position: relative;
      display: inline-block;
      text-align: center;
      text-decoration: none;
      text-overflow: ellipsis;
      white-space: nowrap;
    `,

    sourceName: css`
      display: flex;
      align-items: center;
    `,

    statusTagContainer: css`
      margin-right: 8px;
      display: inherit;
    `,

    statusTag: css`
      height: 24px;
      padding: 5px 8px;
      border-radius: 2px;
    `,

    pagedUsers: css`
      width: 100%;
    `,

    // TODO: Where are trash-button/hover-button coming from?
    pagedUsersList: css`
      list-style-type: none;
      margin-bottom: 20px;
      width: 100%;

      & > li .trash-button {
        display: none;
      }

      & > li:hover .trash-button {
        display: block;
      }

      & > li {
        padding: 8px 12px;
        width: 100%;

        & .hover-button {
          display: none;
        }
      }

      & > li:hover {
        background: ${theme.colors.background.secondary};

        & .hover-button {
          display: inline-flex;
        }
      }
    `,

    userBadge: css`
      vertical-align: middle;
    `,
  };
};
