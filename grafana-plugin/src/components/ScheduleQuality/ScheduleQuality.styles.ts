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

      &--danger {
        // TODO: emotionjs
        background-color: var(--tag-background-danger);
        color: var(--tag-text-danger);
        border: 1px solid var(--tag-border-danger);
      }

      &--warning {
        // TODO: emotionjs
        background-color: var(--tag-background-warning);
        color: var(--tag-text-warning);
        border: 1px solid var(--tag-border-warning);
      }

      &--primary {
        // TODO: emotionjs
        background-color: var(--tag-background-success);
        color: var(--tag-text-success);
        border: 1px solid var(--tag-border-success);
      }
    `,
  };
};
