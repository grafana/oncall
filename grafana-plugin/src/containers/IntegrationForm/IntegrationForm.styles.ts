import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getIntegrationFormStyles = (theme: GrafanaTheme2) => {
  return {
    form: css`
      width: 100%;
    `,

    extraFields: css`
      padding: 12px;
      margin-bottom: 24px;
      border: 1px solid ${theme.colors.border.weak};
      border-radius: 2px;
    `,

    extraFieldsRadio: css`
      margin-bottom: 12px;
    `,

    extraFieldsIcon: css`
      margin-top: -4px;
    `,

    selectorsContainer: css`
      width: 100%;
      display: flex;
      flex-direction: column;
      margin-bottom: -15px;
    `,

    collapse: css`
      width: 100%;
      margin-bottom: 24px;

      svg {
        color: ${theme.colors.primary.text} !important;
      }
    `,

    serviceNowHeading: css`
      margin-bottom: 16px;
    `,

    webhookTest: css`
      margin-bottom: 16px;
    `,

    webhookSwitch: css`
      display: flex;
      flex-direction: row;
      align-items: center;
      gap: 8px;
      margin-bottom: 24px;
      padding-top: 12px;
    `,

    labels: css`
      margin-bottom: 20px;
    `,

    loader: css`
      margin-bottom: 0;
    `,

    // TODO: figure out grafana bug on border
    textarea: css``,
  };
};
