import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getRotationsStyles = (theme: GrafanaTheme2) => {
  return {
    root: css`
      background: 1px solid ${theme.colors.background.secondary};
      border: ${theme.colors.border.weak};
      display: flex;
      flex-direction: column;
      border-radius: ${theme.shape.radius.default};
    `,

    currentTime: css`
      position: absolute;
      width: 1px;
      background: ${theme.colors.gradients.brandVertical}
      top: 0;
      bottom: 0;
      z-index: 1;
      transition: left 500ms ease;
    `,

    header: css`
      padding: 0 10px;
    `,

    title: css`
      margin: 16px 0;
    `,

    layer: css`
      display: block;
    `,

    rotations: css`
      position: relative;
    `,

    layerTitle: css`
      text-align: center;
      font-weight: 500;
      line-height: 16px;
      padding: 8px;
      background: ${theme.colors.background.secondary};

      &:hover {
        background: rgba(204, 204, 220, 0.12);
      }
    `,

    rotationsPlusTitle: css`
      display: flex;
      flex-direction: column;
    `,

    headerPlusContent: css`
      position: relative;
      padding-top: 26px;
      padding-bottom: 26px;
    `,

    layerHeader: css`
      padding: 12px;
      display: flex;
      justify-content: space-between;
    `,

    layerHeaderTitle: css`
      font-weight: 400;
      font-size: 14px;
      line-height: 20px;
      color: rgba(204, 204, 220, 0.65);
    `,

    layerContent: css`
      position: relative;
    `,

    addRotationsLayer: css`
      font-weight: 400;
      font-size: 12px;
      line-height: 16px;
      text-align: center;
      padding: 12px;
      cursor: pointer;

      &:hover {
        background: ${theme.colors.background.secondary};
      }
    `,
  };
};
