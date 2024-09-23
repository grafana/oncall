import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getRotationFormStyles = (theme: GrafanaTheme2) => {
  return {
    container: css`
      margin: 15px 0;
      padding: 15px 0;
      border-top: 1px solid ${theme.colors.border.medium};
      border-bottom: 1px solid ${theme.colors.border.medium};
      width: 100%;
      max-height: 56vh;
      overflow-y: auto;

      @media (max-height: 768px) {
        max-height: 45vh;
      }

      @media (max-height: 868px) {
        max-height: 48vh;
      }

      @media (max-height: 968px) {
        max-height: 52vh;
      }
    `,

    overrideFormContent: css`
      padding: 15px 0;
    `,

    twoFields: css`
      display: flex;
      gap: 8px;
      align-items: flex-start;
      width: 100%;
      > div {
        width: 50;
      }
    `,

    inlineSwitch: css`
      height: 18px;
    `,

    activePeriods: css`
      width: 100%;
    `,

    activePeriodsContent: css`
      padding-top: 8px;
    `,

    timeUnit: css`
      width: 200px;
    `,

    userItem: css`
      position: relative;
    `,

    userTitle: css`
      padding: 6px 10px;
      color: #fff;
      width: 330px;
      overflow: hidden;
      white-space: nowrap;
      position: relative;
    `,

    workingHours: css`
      position: absolute;
      top: 0;
      left: 0;
      height: 100%;
      pointer-events: none;
    `,

    days: css`
      display: flex;
      gap: 14px;
      width: 100%;
    `,

    daysDisabled: css`
      pointer-events: none;
    `,

    day: css`
      width: 28px;
      height: 28px;
      background: ${theme.colors.background.secondary};
      border-radius: 2px;
      line-height: 28px;
      text-align: center;
      cursor: pointer;
    `,

    daySelected: css`
      background: #3d71d9;
    `,

    confirmationModal: css`
      width: 500px;
    `,

    controlError: css`
      border: 1px solid ${theme.colors.error.text};
    `,

    updatedShiftInfo: css`
      margin-bottom: 10px;
      width: 100%;
    `,
  };
};
