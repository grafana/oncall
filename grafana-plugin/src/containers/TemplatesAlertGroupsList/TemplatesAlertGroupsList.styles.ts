import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { Colors } from 'styles/utils.styles';

export const getTemplatesAlertGroupsListStyles = (theme: GrafanaTheme2) => {
  return {
    templateBlockTitle: css`
      padding: 16px;
      align-items: baseline;
      min-height: 56px;
    `,

    templateBlockTitleEditMode: css`
      padding: 16px;
      align-items: baseline;
      min-height: 56px;
      background-color: ${theme.colors.background.secondary};
    `,

    templateBlockList: css`
      width: 30%;
      height: 100%;
      max-width: 100%;
    `,

    alertGroupPayloadView: css`
      background-color: ${theme.colors.background.primary};
      border: none;
      padding-left: 0;
    `,

    alertGroupsList: css`
      padding: 0 16px;

      button {
        padding-left: 0;
      }
    `,

    alertGroupsListItem: css`
      cursor: pointer;
      margin-bottom: 8px;

      &:hover {
        background-color: ${theme.colors.background.secondary};
      }
    `,

    alertGroupsEditor: css`
      height: calc(100% - 60px);

      div[aria-label='Code editor container'] {
        border-bottom: none;
        border-right: none;
      }
    `,

    alertGroupsEditorWithBadge: css`
      height: calc(100% - 60px);

      div[aria-label='Code editor container'] {
        background-color: ${theme.isLight ? Colors.HOVER : Colors.GRAY_9};
        border-bottom: none;
        border-right: none;
        padding-top: 52px;
      }
    `,

    noAlertGroupsBadge: css`
      display: flex;
      padding: 8px;
      align-items: center;

      > div {
        margin-right: 8px;
      }
    `,

    alertGroupsLastPayloadBadge: css`
      position: fixed;
      z-index: 1;
      margin: 16px;
    `,

    selectedAlertName: css`
      text-overflow: ellipsis;
      white-space: nowrap;
      overflow: hidden;
    `,

    selectedAlertNameContainer: css`
      display: flex;
      align-items: center;
      justify-content: space-between;
    `,

    titleActionIcons: css`
      display: flex;
      align-items: center;
      gap: 4px;
    `,
  };
};
