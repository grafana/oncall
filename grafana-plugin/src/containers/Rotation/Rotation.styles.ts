import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getRotationStyles = (theme: GrafanaTheme2) => {
  return {
    root: css`
      transition: background-color 300ms;
      min-height: 28px;
      overflow-x: hidden;
    `,

    loader: css`
      height: 28px;
      display: flex;
      align-items: center;
      justify-content: center;
      width: 100%;

      &:hover {
        background: ${theme.colors.background.secondary};
      }
    `,

    timeline: css`
      display: flex;
      flex-direction: column;
      gap: 5px;
      padding-bottom: 4px;
      position: relative;
    `,

    slots: css`
      width: 100%;
      display: flex;
      transition: opacity 500ms ease;
      opacity: 1;
    `,

    slotsTransparent: css`
      opacity: 0.5;
    `,

    currentTime: css`
      position: absolute;
      left: 450px;
      width: 1px;
      background: ${theme.colors.gradients.brandVertical};
      top: -10px;
      bottom: -10px;
      z-index: 1;
    `,

    empty: css`
      height: 28px;
      cursor: pointer;
      text-align: center;
      margin: 0 2px;
    `,

    pointer: css`
      position: absolute;
      top: -9px;
      transition: left 500ms ease, opacity 500ms ease, transform 500ms ease;
      transform-origin: bottom center;
      opacity: 0;
      transform: scale(0);

      &--active {
        opacity: 1;
        transform: scale(1);
      }
    `,
  };
};
