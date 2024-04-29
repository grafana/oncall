import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getScheduleQualityStyles = (_theme: GrafanaTheme2) => {
  return {
    root: css`
      display: flex;
      flex-direction: row;
      align-items: center;
      gap: 5px;
    `,

    quality: css`
      line-height: 16px;
    `,

    tag: css`
      font-size: 12px;
      padding: 5px 10px;
    `,
  };
};
