import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { COLORS } from 'styles/utils.styles';

const radius = '2px' as string;

export const getScheduleQualityProgressBarStyles = (theme: GrafanaTheme2) => {
  return {
    wrapper: css`
      width: 100%;
      height: 8px;
      display: flex;
      gap: 2px;
    `,

    bar: css`
      height: 8px;

      &--warning {
        backgorund-color: ${theme.colors.warning.main};
      }

      &--danger {
        background-color: ${theme.colors.error.main};
      }

      &--primary {
        background-color: ${theme.colors.success.main};
      }
    `,

    row: css`
      background-color: ${COLORS.GRAY_8};

      &:first-child,
      &:first-child > .bar {
        border-top-left-radius: ${radius};
        border-bottom-left-radius: ${radius};
      }

      &:last-child,
      &:last-child > .bar {
        border-top-right-radius: ${radius};
        border-bottom-right-radius: ${radius};
      }
    `,
  };
};
