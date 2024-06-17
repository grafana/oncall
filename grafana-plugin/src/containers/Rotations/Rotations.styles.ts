import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getRotationsStyles = (theme: GrafanaTheme2) => {
  return {
    root: css`
      background: ${theme.colors.background.secondary};
      border: 1px solid ${theme.colors.border.weak};
      display: flex;
      flex-direction: column;
      border-radius: 2px;

      &--withNoBackgroundAndBorder {
        background: none;
        border: none;
      }
    `,

    currentTime: css`
      position: absolute;
      width: 1px;
      background: ${theme.colors.gradients.brandVertical};
      top: 0;
      bottom: 0;
      z-index: 1;
    `,

    header: css`
      padding: 12px;
    `,

    layer: css`
      display: block;
    `,

    layerFirst: css`
      padding-top: 32px;
    `,

    layerTitle: css`
      margin: 8px;
      border: ${theme.colors.border.weak};
      background: ${theme.colors.background.canvas};
    `,

    rotationsPlusTitle: css`
      display: flex;
      flex-direction: column;
    `,

    layerContent: css`
      position: relative;
    `,

    addRotationsLayer: css`
      font-weight: 400;
      font-size: 12px;
      line-height: 16px;
      text-align: left;
      padding: 12px;
      cursor: pointer;

      &:hover {
        background: ${theme.colors.background.secondary};
      }
    `,
  };
};
