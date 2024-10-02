import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getTimelineMarksStyles = (theme: GrafanaTheme2) => {
  return {
    root: css`
      position: absolute;
      display: flex;
      width: 100%;
      top: 0;
      bottom: 0;
      font-weight: 400;
      font-size: 12px;
      lineheight: 16px;
      pointer-events: none;
    `,
    rootBorderBottom: css`
      borderbottom: 1px solid ${theme.colors.border.medium};
    `,

    weekday: css`
      display: flex;
      flex-direction: column;
      justify-content: space-between;

      &:not(:last-child) {
        border-right: 1px solid ${theme.colors.border.medium};
      }
    `,

    weekdayEnd: css`
      background: ${theme.isLight ? 'rgba(204, 204, 220, 0.11)' : 'rgba(204, 204, 220, 0.04)'};
    `,

    weekdayTitle: css`
      width: 100%;
      text-align: center;
      padding-top: 4px;
      flex-grow: 1;
    `,

    debugScale: css`
      position: absolute;
      top: -6px;
      width: 100%;
      right: 0;
    `,
  };
};
