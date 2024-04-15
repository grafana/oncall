import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getStyles = (theme: GrafanaTheme2) => ({
  urlIntegrationBlock: css`
    margin-bottom: 32px;
  `,
  urlInput: css`
    height: 25px;
    background: ${theme.colors.background.canvas};

    & input {
      height: 25px;
    }
  `,
  form: css`
    height: 100%;
    padding-top: 32px;
  `,
  formFieldsWrapper: css`
    width: 100%;
  `,
  sourceCodeRoot: css`
    min-height: 200px;
    height: calc(100vh - 550px);
  `,
  noWebhooksInfo: css`
    margin: 24px 0 12px;
  `,
  infoIcon: css`
    margin-left: 4px;
  `,
  monacoEditorLabelWrapper: css`
    display: flex;
    width: 100%;
  `,
  switcherFieldWrapper: css`
    display: flex;
    gap: 8px;
    align-items: center;
  `,
  switcherLabel: css`
    margin-bottom: 0;
  `,
  selectField: css`
    width: 200px;
    margin-bottom: 0;
  `,
  hamburgerIcon: css`
    background: ${theme.colors.secondary.shade};
  `,
  horizontalGroup: css`
    display: flex;
    gap: 8px;
  `,
  openConfigurationBtn: css`
    background: ${theme.colors.secondary.shade};
  `,
  outgoingWebhooksTable: css`
    margin: 24px 0;
  `,
  backsyncColumn: css`
    display: flex;
    justify-content: flex-end;

    & label {
      position: relative;
    }
  `,
  triggerTemplateWrapper: css`
    position: relative;
    width: 100%;
  `,
  addTriggerTemplate: css`
    margin-bottom: 16px;
  `,
  editTriggerTemplateBtn: css`
    position: absolute;
    top: -8px;
    right: 0;
  `,
  searchIntegrationsInput: css`
    margin-bottom: 24px;
  `,
  tabsWrapper: css`
    padding: 16px 16px 0 8px;
    height: calc(100vh - 135px); // 135px is a grafana + drawer header
    overflow: auto;
  `,
  connectIntegrationModalContent: css`
    padding-bottom: 0;
  `,
  connectIntegrationModalButtons: css`
    margin-top: 50px;
  `,
});
