import { css } from '@emotion/css';

export const getSlackSettingsStyles = () => ({
  title: css`
    margin-bottom: 20px;
  `,

  stub: css`
    width: 100%;
    padding: 50px 0;
  `,

  rootSelect: css`
    width: 400px;
  `,

  slackSettings: css`
    border-bottom: 1px solid rgba(204, 204, 220, 0.25);
  `,

  slackInfoblock: css`
    text-align: center;
    width: 100%;
  `,

  externalLinkStyle: css`
    margin-right: 4px;
    align-self: baseline;
  `,

  teamWorkspace: css`
    height: 30px;
  `,

  infoblockText: css`
    margin-left: 48px;
    margin-right: 48px;
  `,

  marginTop: css`
    margin-top: 24px;
  `,

  upgradeSlackBtn: css`
    position: absolute;
    right: 20px;
    top: 50%;
    transform: translateY(-50%);
  `,

  upgradeSlackAlertText: css`
    margin-right: 110px;

    a {
      font-weight: 600;
    }
  `,

  linkToIncidentWrapper: css`
    margin-top: 16px;
  `,

  confirmUninstallModal: css`
    input {
      min-width: 300px;
    }
  `,

  root: css`
    select {
      width: 400px;
    }
  `,
});
