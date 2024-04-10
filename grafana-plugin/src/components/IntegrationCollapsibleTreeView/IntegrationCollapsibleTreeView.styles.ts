import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { COLORS } from 'styles/utils.styles';

export const getIntegrationCollapsibleTreeStyles = (theme: GrafanaTheme2) => {
  return {
    container: css`
      margin-left: 32px;
      position: relative;
    `,

    element: css`
      margin-left: 16px;
      visibility: hidden;
      overflow-y: hidden;
      height: 0;

      &--visible {
        visibility: visible;
        height: auto;
        overflow: unset;
      }
    `,

    group: css`
      position: relative;
      padding-bottom: 12px;

      &:not(:last-child):before {
        content: '';
        position: absolute;
        height: 100%;
        border: 1px solid ${theme.colors.border.weak};
        margin-top: 4px;
        margin-left: -19px;
        top: 20px;
      }

      &--hidden {
        display: none;
      }
    `,

    timeline: css`
      [data-emotion='group']::before {
        margin-left: -18px;
        border: 0 !important;
        width: 4px;
        background-color: ${theme.colors.border.medium};
      }
    `,

    icon: css`
      position: absolute;
      top: 0;
      left: -30px;
      color: ${COLORS.ALWAYS_GREY};
      width: 28px;
      height: 28px;
      text-align: center;
      background-color: ${theme.colors.background.primary} !important;
      border: 1px solid ${theme.colors.background.primary};
      z-index: 100;
      border-radius: 4px;
      padding: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-top: 4px;

      path {
        // this will overwrite all icons below to be gray
        fill: ${COLORS.ALWAYS_GREY};
      }
    `,

    numberIcon: css`
      width: 28px;
      height: 28px;
      border-radius: 50%;
      text-align: center;
      line-height: 28px;
      font-size: 14px;
      font-weight: 400;
      color: ${theme.colors.text.primary};
      background-color: ${theme.colors.border.medium};
      flex-shrink: 0;
      margin: 0;
    `,
  };
};
