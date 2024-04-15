import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getAvatarStyles = (_theme: GrafanaTheme2) => {
  return {
    avatar: css`
      display: inline-block;
      border-radius: 50%;
      overflow: hidden;

      &--xs {
        width: 12px;
        height: 12px;
      }

      &--small {
        width: 16px;
        height: 16px;
      }

      &--medium {
        width: 24px;
        height: 24px;
      }

      &--large {
        width: 32px;
        height: 32px;
      }
    `,
  };
};
