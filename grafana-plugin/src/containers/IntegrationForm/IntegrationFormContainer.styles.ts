import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getIntegrationFormContainerStyles = (theme: GrafanaTheme2) => {
  return {
    content: css`
      margin: 4px 4px 50px 4px;
      padding-bottom: 24px;
    `,

    cards: css`
      display: flex;
      flex-wrap: wrap;
      gap: 24px;
      overflow: auto;
      scroll-snap-type: y mandatory;
      width: 100%;
    `,

    cardsCentered: css`
      justify-content: center;
      align-items: center;
    `,

    card: css`
      width: 48%;
      height: 88px;
      scroll-snap-align: start;
      scroll-snap-stop: normal;
      display: flex;
      flex-direction: row;
      align-items: center;
      justify-content: flex-start;
      cursor: pointer;
      position: relative;
      gap: 20px;
    `,

    cardFeatured: css`
      width: 100%;
      height: 106px;
      cursor: pointer;
    `,

    title: css`
      margin: 10px 0 10px 0;
      max-width: 500px;
    `,

    footer: css`
      display: block;
      margin-top: 10px;
    `,

    searchIntegration: css`
      width: 100%;
      margin-bottom: 24px;
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
  };
};
