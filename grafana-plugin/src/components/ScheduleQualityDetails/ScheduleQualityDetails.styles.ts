import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

const padding = '8px';
const width = '340px';

export const getScheduleQualityDetailsStyles = (_theme: GrafanaTheme2) => {
  return {
    root: css`
      width: ${width};
      margin-left: -8px;
      margin-right: -8px;
    `,

    container: css`
      display: flex;
      flex-wrap: wrap;
      flex-direction: column;
      width: 100%;

      &--withTopPadding {
        padding-top: ${padding};
      }

      &--withLateralPadding {
        padding-left: ${padding};
        padding-right: ${padding};
      }
    `,

    header: css`
      padding-bottom: calc(${padding} / 2);
    `,

    headerSubText: css`
      font-weight: 500;
    `,

    row: css`
      display: flex;
      flex-direction: row;
      column-gap: 8px;
      margin-bottom: 4px;
    `,

    metholodogy: css`
      padding: 4px 0;
    `,

    text: css`
      word-wrap: break-word;
      padding-left: 24px;
    `,

    username: css`
      max-width: calc(${width} - ${padding});
      white-space: nowrap;
      text-overflow: ellipsis;
      overflow: hidden;
    `,
  };
};
