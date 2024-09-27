import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getUserTimezonesStyles = (theme: GrafanaTheme2) => {
  return {
    root: css`
      border: 1px solid ${theme.colors.border.weak};
      display: flex;
      flex-direction: column;
      background: ${theme.colors.background.secondary};
      border-radius: 2px;
      position: relative;
    `,

    shades: css`
      background: repeating-linear-gradient(
        -45deg,
        ${theme.colors.background.secondary},
        ${theme.colors.background.secondary} 2px,
        transparent 2px,
        transparent 6px
      );
      height: 100%;
      position: absolute;
    `,

    workingHours: css`
      position: absolute;
      height: 100%;
    `,

    content: css`
      z-index: 1;
    `,

    header: css`
      padding: 0 10px;
    `,

    title: css`
      font-weight: 400;
      font-size: 19px;
      line-height: 24px;
      color: rgba(204, 204, 220, 0.65);
      margin-top: 16px;
    `,

    currentTime: css`
        position: absolute;
        left: 0;
        width: 1px;
        background: ${theme.colors.gradients.brandVertical}
        top: 0;
        bottom: 0;
        z-index: 0;
    `,

    users: css`
      position: relative;
      height: 76px;
      overflow: hidden;
    `,

    usersPlaceholder: css`
      width: 100%;
      text-align: center;
    `,

    icon: css`
      color: ${theme.colors.secondary.text};
    `,

    avatarGroup: css`
      position: absolute;
      top: 10px;
      height: 32px;
    `,

    avatar: css`
      position: absolute;
      top: 0;
      transition: opacity 200ms ease, left 200ms ease;
      border-radius: 50%;
    `,

    isOncallIcon: css`
      color: ${theme.isDark ? '#181b1f' : '#fff'};
      position: absolute;
      left: -1px;
      bottom: -1px;
    `,

    userMore: css`
      position: absolute;
      padding: 0 5px;
      bottom: 0;
      font-size: 12px;
      line-height: 16px;
      background: #454952;
      color: #ccccdc;
      border-radius: 8px;
      text-align: center;
      transition: opacity 200ms ease, left 200ms ease;
      pointer-events: none;
    `,

    avatarGroupInactive: css`
      pointer-events: none;
      opacity: 0.2;
      transition: opacity 0.5s ease;
    `,

    timeMarksWrapper: css`
      position: relative;
    `,

    timeMarks: css`
      position: absolute;
      top: -20px;
      display: flex;
      font-weight: 400;
      line-height: 20px;
      color: rgba(204, 204, 220, 0.65);
      width: 100%;
    `,

    timeMarkText: css`
      display: inline-block;
      padding: 0 5px;
    `,

    timeMarkTextTranslated: css`
      transform: translate(-50%, 0);
      padding: 0;
    `,

    timeMark: css`
      $:last-child {
        position: absolute;
        right: 0;
      }
    `,
  };
};
