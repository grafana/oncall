import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getAddRespondersStyles = (theme: GrafanaTheme2) => {
  return {
    content: css`
      width: 100%;
      position: relative;
    `,

    respondersList: css`
      padding-top: 8px;
      list-style-type: none;
      margin-bottom: 20px;
      width: 100%;

      & > li .hover-button {
        display: none;
      }

      & > li:hover .hover-button {
        display: inline-flex;
      }

      & > li {
        padding: 10px 12px;
        width: 100%;
      }

      & > li:hover {
        background: ${theme.colors.background.secondary};
      }
    `,

    alert: css`
      padding-top: 4px;
    `,

    timelineIconBackground: css`
      width: 28px;
      height: 28px;
      border-radius: 50%;
      display: flex;
      justify-content: center;
      align-items: center;
      background: rgba(${theme.isDark ? '70, 76, 84, 1' : '70, 76, 84, 0'});

      & > img {
        width: 100%;
        height: 100%;
      }

      &--green {
        background: #299c46;
      }
    `,

    responderName: css`
      max-width: 250px;
      overflow: hidden;
      white-space: nowrap;
    `,

    confirmParticipantInvitationModal: css`
      max-width: 550px;
    `,

    confirmParticipantInvitationModalSelect: css`
      display: inline-flex;
      margin: 0 4px;
    `,

    learnMoreLink: css`
      display: inline-block;
    `,
  };
};
