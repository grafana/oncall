import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

export const getStyles = (theme: GrafanaTheme2) => ({
  urlIntegrationBlock: css({
    marginBottom: '32px',
  }),
  urlInput: css({
    height: '25px',
    background: theme.colors.background.canvas,
    '& input': {
      height: '25px',
    },
  }),
  form: css({
    height: '100%',
    paddingTop: '32px',
  }),
  formFieldsWrapper: css({
    width: '100%',
  }),
  sourceCodeRoot: css({
    minHeight: '200px',
    height: 'calc(100vh - 550px)',
  }),
  infoIcon: css({
    marginLeft: '4px',
  }),
  monacoEditorLabelWrapper: css({
    display: 'flex',
    width: '100%',
  }),
  switcherFieldWrapper: css({
    display: 'flex',
    gap: '8px',
    alignItems: 'center',
  }),
  switcherLabel: css({
    marginBottom: 0,
  }),
  selectField: css({
    width: '200px',
    marginBottom: 0,
  }),
  hamburgerIcon: css({
    background: theme.colors.secondary.shade,
  }),
  horizontalGroup: css({
    display: 'flex',
    gap: '8px',
  }),
  openConfigurationBtn: css({
    background: theme.colors.secondary.shade,
  }),
  outgoingWebhooksTable: css({
    margin: '24px 0',
  }),
  backsyncColumn: css({
    display: 'flex',
    justifyContent: 'flex-end',
    '& label': {
      position: 'relative',
    },
  }),
  triggerTemplateWrapper: css({
    position: 'relative',
    width: '100%',
  }),
  addTriggerTemplate: css({
    marginBottom: '16px',
  }),
  editTriggerTemplateBtn: css({
    position: 'absolute',
    top: '-8px',
    right: 0,
  }),
  searchIntegrationsInput: css({
    marginBottom: '24px',
  }),
  tabsWrapper: css({
    padding: '16px 16px 0 8px',
  }),
  connectIntegrationModalContent: css({
    paddingBottom: 0,
  }),
  connectIntegrationModalButtons: css({
    marginTop: '50px',
  }),
});
